# ./factcheck/core/ClaimVerify.py

from __future__ import annotations

import json
import time
from factcheck.utils.logger import CustomLogger
from factcheck.utils.data_class import Evidence

logger = CustomLogger(__name__).getlog()


class ClaimVerify:
    def __init__(self, llm_client, prompt):
        self.llm_client = llm_client
        self.prompt = prompt

    def verify_claims(self, claim_evidences_dict, prompt: str = None) -> dict[str, list[Evidence]]:
        """
        Verifies the factuality of claims against their corresponding evidences using a batching approach.
        """
        return self._batch_verify_claims(claim_evidences_dict, prompt=prompt)

    def _batch_verify_claims(
        self,
        claim_evidences_dict: dict[str, list[dict]],
        num_retries=3,
        prompt: str = None,
    ) -> dict[str, list[Evidence]]:
        """
        Verifies claims by batching all evidences for a single claim into one LLM call.
        """
        claim_verifications_dict = {k: [] for k in claim_evidences_dict.keys()}
        total_claims = len(claim_evidences_dict)
        
        for i, (claim, evidences) in enumerate(claim_evidences_dict.items()):
            logger.info(f"Verifying claim {i+1}/{total_claims}: '{claim[:70]}...' with {len(evidences)} evidences.")
            
            if not evidences:
                continue

            if i > 0:
                time.sleep(2)

            evidences_for_prompt = []
            for j, evi in enumerate(evidences):
                evidences_for_prompt.append({
                    "id": f"E{j + 1}",
                    "text": evi.get('text', ''),
                    "trust_level": evi.get('trust_level', 'unknown')
                })

            evidences_json_str = json.dumps(evidences_for_prompt, indent=2)
            
            # --- START: SỬA LỖI KEYERROR DỨT ĐIỂM ---
            # Lấy template gốc
            prompt_template = self.prompt.batch_verify_prompt if prompt is None else prompt
            
            # 1. Thay thế placeholder `{claim}` trước
            prompt_with_claim = prompt_template.replace("{claim}", claim)
            
            # 2. Thay thế placeholder `{evidences_json}` sau
            # Cách này đảm bảo rằng .format() hay .replace() không bị xung đột
            # với nội dung của chuỗi JSON.
            user_input = prompt_with_claim.replace("{evidences_json}", evidences_json_str)
            # --- END: SỬA LỖI KEYERROR DỨT ĐIỂM ---
            
            messages = self.llm_client.construct_message_list([user_input])
            response = self.llm_client.call(messages, num_retries=num_retries)
            
            try:
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:-3].strip()
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:-3].strip()
                
                response_json = json.loads(cleaned_response)
                verifications = response_json.get("verifications", [])
                
                for verification in verifications:
                    try:
                        evidence_id = verification.get("id")
                        if evidence_id and evidence_id.startswith("E"):
                            original_evidence_index = int(evidence_id[1:]) - 1
                            if 0 <= original_evidence_index < len(evidences):
                                original_evidence = evidences[original_evidence_index]
                                
                                final_evidence = Evidence(
                                    claim=claim,
                                    text=original_evidence.get('text', ''),
                                    url=original_evidence.get('url', 'N/A'),
                                    reasoning=verification.get("reasoning", "[No reasoning provided]"),
                                    relationship=verification.get("relationship", "IRRELEVANT")
                                )
                                claim_verifications_dict[claim].append(final_evidence)
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Could not map verification back to original evidence: {verification}. Error: {e}")

            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Warning: LLM response parse fail for batch verification. Error: {e}. Response was: {response}")
                for evi in evidences:
                    claim_verifications_dict[claim].append(Evidence(
                        claim=claim, text=evi.get('text', ''), url=evi.get('url', 'N/A'),
                        reasoning="[System Warning] Failed to parse LLM response.", relationship="IRRELEVANT"
                    ))

        return claim_verifications_dict