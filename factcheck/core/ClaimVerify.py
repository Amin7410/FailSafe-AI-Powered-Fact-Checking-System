# ./factcheck/core/ClaimVerify.py

from __future__ import annotations
import json
from collections import Counter
from factcheck.utils.logger import CustomLogger
from factcheck.utils.data_class import Evidence

logger = CustomLogger(__name__).getlog()


class ClaimVerify:
    def __init__(self, llm_client, prompt):
        self.llm_client = llm_client
        self.prompt = prompt

    def verify_claims(self, claim_evidences_dict, batch_size: int = 5) -> dict[str, list[Evidence]]:
        claims_to_verify = [claim for claim, evidences in claim_evidences_dict.items() if evidences]
        if not claims_to_verify:
            return {k: [] for k in claim_evidences_dict.keys()}
        
        logger.info(f"Starting COUNCIL verification for {len(claims_to_verify)} claims.")
        final_verifications_dict = {k: [] for k in claim_evidences_dict.keys()}
        
        for i in range(0, len(claims_to_verify), batch_size):
            batch_claims = claims_to_verify[i : i + batch_size]
            logger.info(f"Processing verification batch {i//batch_size + 1}: {len(batch_claims)} claims.")

            all_prompts = []
            meta_map = []  
            for claim in batch_claims:
                evidences = claim_evidences_dict[claim]
                
                evidences_clean = [
                    {
                        "id": f"E{j + 1}", 
                        "text": evi.get('text', '')[:1000],  
                        "trust_level": evi.get('trust_level', 'unknown')
                    } 
                    for j, evi in enumerate(evidences)
                ]
                evidences_json_str = json.dumps(evidences_clean)
                roles = [
                    ("Logician", self.prompt.logician_prompt),
                    ("Researcher", self.prompt.researcher_prompt),
                    ("Skeptic", self.prompt.skeptic_prompt)
                ]
                for role_name, role_template in roles:
                    user_input = role_template.format(claim=claim, evidences_json=evidences_json_str)
                    all_prompts.append(user_input)
                    meta_map.append({"claim": claim, "role": role_name})
            logger.info(f"Council is debating... Sending {len(all_prompts)} requests.")
            messages_list = self.llm_client.construct_message_list(all_prompts)
            
            responses = self.llm_client.multi_call(
                messages_list, 
                num_retries=3,
                schema_type="verification" 
            )
            results_by_claim = {c: {} for c in batch_claims}
            for idx, response in enumerate(responses):
                meta = meta_map[idx]
                claim = meta['claim']
                role = meta['role']
                try:
                    if response:
                        data = json.loads(response)
                        verifications = data.get("verifications", [])
                        
                        for v in verifications:
                            e_id = v.get("id")
                            if not e_id: 
                                continue
                            
                            if e_id not in results_by_claim[claim]:
                                results_by_claim[claim][e_id] = []
                            
                            results_by_claim[claim][e_id].append({
                                "role": role,
                                "relationship": v.get("relationship", "IRRELEVANT").upper(),
                                "reasoning": v.get("reasoning", "No reasoning provided.")
                            })
                except Exception as e:
                    logger.warning(f"Agent {role} failed parse on claim '{claim[:20]}...': {e}")

            for claim in batch_claims:
                original_evidences = claim_evidences_dict[claim]
                final_evidence_objs = []
                
                for j, evi_orig in enumerate(original_evidences):
                    e_id = f"E{j + 1}"
                    opinions = results_by_claim[claim].get(e_id, [])
                    
                    if not opinions:
                        final_obj = Evidence(
                            claim=claim, text=evi_orig.get('text'), url=evi_orig.get('url'),
                            reasoning="[System] No AI agents verified this evidence.", relationship="IRRELEVANT"
                        )
                    else:
                        votes = [op['relationship'] for op in opinions]
                        vote_counts = Counter(votes)
                        final_relationship = vote_counts.most_common(1)[0][0]
                        combined_reasoning = " || ".join([f"[{op['role']}]: {op['reasoning']}" for op in opinions])
                        
                        final_obj = Evidence(
                            claim=claim,
                            text=evi_orig.get('text', ''),
                            url=evi_orig.get('url', 'N/A'),
                            relationship=final_relationship,
                            reasoning=combined_reasoning
                        )
                    final_evidence_objs.append(final_obj)
                final_verifications_dict[claim] = final_evidence_objs
        return final_verifications_dict