# ./factcheck/core/CheckWorthy.py

from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()


class Checkworthy:
    def __init__(self, llm_client, prompt):
        """Initialize the Checkworthy class

        Args:
            llm_client (BaseClient): The LLM client used for identifying checkworthiness of claims.
            prompt (BasePrompt): The prompt used for identifying checkworthiness of claims.
        """
        self.llm_client = llm_client
        self.prompt = prompt

    def identify_checkworthiness(self, texts: list[str], num_retries: int = 3, prompt: str = None) -> tuple[list[str], dict]:
        """Use Gemini to identify whether candidate claims are worth fact checking. if gpt is unable to return correct checkworthy_claims, we assume all texts are checkworthy.

        Args:
            texts (list[str]): a list of texts to identify whether they are worth fact checking
            num_retries (int, optional): maximum attempts for Gemini to identify checkworthy claims. Defaults to 3.

        Returns:
            tuple[list[str], dict]: a list of checkworthy claims, and a dictionary of all claims with their reasons.
        """
        checkworthy_claims = []
        claim2checkworthy = {text: "No (Failed to get a valid response from LLM)" for text in texts}

        joint_texts = "\n".join([str(i + 1) + ". " + j for i, j in enumerate(texts)])

        if prompt is None:
            user_input = self.prompt.checkworthy_prompt.format(texts=joint_texts)
        else:
            user_input = prompt.format(texts=joint_texts)

        messages = self.llm_client.construct_message_list([user_input])
        for i in range(num_retries):
            response = self.llm_client.call(messages, num_retries=1, seed=42 + i)
            try:
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:-3].strip()
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:-3].strip()

                claim2checkworthy = eval(cleaned_response)
                
                valid_answer = list(
                    filter(
                        lambda x: x[1].lower().startswith("yes") or x[1].lower().startswith("no"),
                        claim2checkworthy.items(),
                    )
                )
                
                if len(valid_answer) == len(claim2checkworthy):
                    temp_checkworthy = list(filter(lambda x: x[1].lower().startswith("yes"), claim2checkworthy.items()))
                    checkworthy_claims = [item[0] for item in temp_checkworthy]
                    break 
            except Exception as e:
                logger.error(f"====== Error: {e}, the LLM response is: {response}")
                logger.error(f"====== Our input is: {messages}")
        
        if not checkworthy_claims:
            logger.warning("Could not determine checkworthiness from LLM, assuming all claims are checkworthy.")
            checkworthy_claims = []
        
        return checkworthy_claims, claim2checkworthy