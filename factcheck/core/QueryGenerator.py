# ./factcheck/core/QueryGenerator.py

import time
import json
from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()


class QueryGenerator:
    def __init__(self, llm_client, prompt, max_query_per_claim: int = 5):
        """
        Initializes the QueryGenerator class.

        Args:
            llm_client (BaseClient): The LLM client used for generating questions.
            prompt (BasePrompt): The prompt used for generating questions.
            max_query_per_claim (int): The maximum number of queries to generate per claim.
        """
        self.llm_client = llm_client
        self.prompt = prompt
        self.max_query_per_claim = max_query_per_claim

    def generate_query(self, claims: list[str], generating_time: int = 3, prompt: str = None) -> dict[str, list[str]]:
        """
        Generates search queries for the given claims sequentially to respect API rate limits.

        Args:
            claims (list[str]): A list of claims to generate questions for.
            generating_time (int, optional): Maximum retry attempts for the LLM call. Defaults to 3.
            prompt (str, optional): An alternative prompt template to use. Defaults to None.

        Returns:
            dict: A dictionary mapping each claim to a list of generated search queries.
        """
        claim_query_dict = {}

        if not claims:
            return {}

        logger.info(f"Starting query generation for {len(claims)} claims.")

        # --- LOGIC ĐÃ ĐƯỢC THAY THẾ BẰNG VÒNG LẶP TUẦN TỰ ---
        for i, claim in enumerate(claims):
            logger.info(f"Generating query for claim {i+1}/{len(claims)}: '{claim[:70]}...'")

            # Add a delay between API calls to stay within rate limits (e.g., 10 RPM = 6s/request)
            # No delay for the first request.
            if i > 0:
                time.sleep(6)

            # Determine which prompt to use
            if prompt is None:
                user_input = self.prompt.qgen_prompt.format(claim=claim)
            else:
                user_input = prompt.format(claim=claim)

            # Construct the message for the LLM
            messages = self.llm_client.construct_message_list([user_input])
            
            # Use the single .call method which has built-in retries
            response = self.llm_client.call(messages, num_retries=generating_time)
            
            _questions = []
            try:
                # Safely parse the JSON response from the LLM
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:-3].strip()
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:-3].strip()
                
                response_dict = json.loads(cleaned_response)
                
                # Use .get() for safety and ensure the result is a list
                _questions = response_dict.get("Questions", [])
                if not isinstance(_questions, list):
                    logger.warning(f"LLM returned non-list for Questions: {_questions}. Defaulting to empty list.")
                    _questions = []
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Warning: LLM response parse fail for query generation. Error: {e}. Response was: '{response}'")

            # Ensure that each claim has at least one query (the claim itself)
            # and respect the max_query_per_claim limit.
            claim_query_dict[claim] = [claim] + _questions[:(self.max_query_per_claim - 1)]

        logger.info("Finished query generation.")
        return claim_query_dict