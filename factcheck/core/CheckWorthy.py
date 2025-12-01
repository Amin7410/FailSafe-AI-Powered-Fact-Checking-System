# ./factcheck/core/CheckWorthy.py

from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()


class Checkworthy:
    def __init__(self, llm_client, prompt):
        self.llm_client = llm_client
        self.prompt = prompt

    def identify_checkworthiness(self, texts: list[str], num_retries: int = 3, prompt: str = None) -> tuple[list[str], dict]:
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