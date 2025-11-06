# ./factcheck/core/ClaimVerify.py (PHIÊN BẢN GỠ LỖI)

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
        claims_to_verify = [claim for claim, evidences in claim_evidences_dict.items() if evidences]
        if not claims_to_verify:
            return {k: [] for k in claim_evidences_dict.keys()}

        logger.info(f"Starting PARALLEL verification for {len(claims_to_verify)} claims.")

        prompts_list = []
        claim_map = {i: claim for i, claim in enumerate(claims_to_verify)}

        for i, claim in enumerate(claims_to_verify):
            evidences = claim_evidences_dict[claim]
            
            evidences_for_prompt = [{"id": f"E{j + 1}", "text": evi.get('text', ''), "trust_level": evi.get('trust_level', 'unknown')} for j, evi in enumerate(evidences)]
            evidences_json_str = json.dumps(evidences_for_prompt, indent=2)
            
            prompt_template = self.prompt.batch_verify_prompt if prompt is None else prompt
            prompt_with_claim = prompt_template.replace("{claim}", claim)
            user_input = prompt_with_claim.replace("{evidences_json}", evidences_json_str)
            
            prompts_list.append(user_input)

        messages_list = self.llm_client.construct_message_list(prompts_list)
        
        logger.info(f"Sending {len(claims_to_verify)} verification requests to LLM concurrently...")
        responses = self.llm_client.multi_call(messages_list=messages_list, num_retries=3)
        logger.info("Received all verification responses from LLM.")
        
        final_verifications_dict = {k: [] for k in claim_evidences_dict.keys()}

        for i, response in enumerate(responses):
            claim = claim_map[i]
            original_evidences = claim_evidences_dict[claim]
            verified_evidences_for_claim = []

            # === THÊM CAMERA GIÁM SÁT VÀO ĐÂY ===
            print("\n" + "=" * 20 + " VERIFY DEBUG " + "=" * 20)
            print(f"Claim: {claim[:80]}...")
            print(f"Raw LLM Response:\n---\n{response}\n---")
            # =======================================

            try:
                if response:
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
                                if 0 <= original_evidence_index < len(original_evidences):
                                    original_evidence = original_evidences[original_evidence_index]
                                    
                                    final_evidence = Evidence(
                                        claim=claim,
                                        text=original_evidence.get('text', ''),
                                        url=original_evidence.get('url', 'N/A'),
                                        reasoning=verification.get("reasoning", "[No reasoning provided]"),
                                        relationship=verification.get("relationship", "IRRELEVANT")
                                    )
                                    verified_evidences_for_claim.append(final_evidence)
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Could not map verification for claim '{claim[:50]}...'. Invalid ID: {verification.get('id')}. Error: {e}")
                else:
                    logger.warning(f"Received an empty/failed response for verification of claim '{claim[:50]}...'.")

            except (json.JSONDecodeError, AttributeError) as e:
                # Ghi log chi tiết hơn về lỗi
                logger.error(f"LLM response PARSE FAIL for claim '{claim[:50]}...'. Error: {e}")
                logger.error(f"Offending Response was: '{response}'")  # Ghi lại response gây lỗi
            
            if not verified_evidences_for_claim:
                for evi in original_evidences:
                    verified_evidences_for_claim.append(Evidence(
                        claim=claim, text=evi.get('text', ''), url=evi.get('url', 'N/A'),
                        reasoning="[System Warning] Failed to parse or receive LLM verification.", relationship="IRRELEVANT"
                    ))

            final_verifications_dict[claim] = verified_evidences_for_claim
        
        print("=" * 54 + "\n")
        return final_verifications_dict