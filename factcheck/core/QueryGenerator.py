# ./factcheck/core/QueryGenerator.py

import time
import json
from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()


class QueryGenerator:
    def __init__(self, llm_client, prompt, max_query_per_claim: int = 5):
        self.llm_client = llm_client
        self.prompt = prompt
        self.max_query_per_claim = max_query_per_claim

    def generate_query(self, claims: list[str], generating_time: int = 3, prompt: str = None, batch_size: int = 15) -> dict[str, list[str]]: # Thêm batch_size
        claim_query_dict = {}

        if not claims:
            return {}

        logger.info(f"Starting PARALLEL query generation for {len(claims)} claims in batches of {batch_size}.")

        for i in range(0, len(claims), batch_size):
            batch_claims = claims[i : i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch_claims)} claims.")
            prompts_list = []
            for claim in batch_claims:
                prompt_template = self.prompt.qgen_prompt if prompt is None else prompt
                user_input = prompt_template.format(claim=claim)
                prompts_list.append(user_input)

            messages_list = self.llm_client.construct_message_list(prompts_list)
            
            logger.info(f"Sending {len(batch_claims)} query generation requests to LLM for this batch...")
            responses = self.llm_client.multi_call(
                messages_list=messages_list, 
                num_retries=generating_time
            )
            logger.info("Received responses for this batch.")
            
            for claim, response in zip(batch_claims, responses):
                _questions = []
                try:
                    if response:
                        cleaned_response = response.strip()
                        if cleaned_response.startswith("```json"):
                            cleaned_response = cleaned_response[7:-3].strip()
                        elif cleaned_response.startswith("```"):
                            cleaned_response = cleaned_response[3:-3].strip()
                        
                        response_dict = json.loads(cleaned_response)
                        
                        _questions = response_dict.get("Questions", [])
                        if not isinstance(_questions, list):
                            logger.warning(f"LLM returned non-list for Questions on claim '{claim[:50]}...'.")
                            _questions = []
                    else:
                        logger.warning(f"Received an empty/failed response for claim '{claim[:50]}...'.")

                except (json.JSONDecodeError, AttributeError) as e:
                    logger.warning(f"Warning: LLM response parse fail for query generation on claim '{claim[:50]}...'. Error: {e}. Response: '{response}'")

                claim_query_dict[claim] = [claim] + _questions[:(self.max_query_per_claim - 1)]
        logger.info("Finished query generation for all batches.")
        return claim_query_dict