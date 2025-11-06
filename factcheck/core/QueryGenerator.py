# ./factcheck/core/QueryGenerator.py (PHIÊN BẢN ĐÃ TỐI ƯU)

import time  # Vẫn giữ lại để có thể dùng trong tương lai, nhưng không còn sleep(6) nữa
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
        [TỐI ƯU] Generates search queries for the given claims in parallel.
        Instead of a sequential loop, it prepares all requests and sends them
        at once using the LLM client's multi_call feature.
        """
        claim_query_dict = {}

        if not claims:
            return {}

        logger.info(f"Starting PARALLEL query generation for {len(claims)} claims.")

        # --- THAY ĐỔI 1: CHUẨN BỊ TẤT CẢ CÁC PROMPT TRƯỚC ---
        # Chúng ta không còn ở trong vòng lặp for nữa.
        # Thay vào đó, chúng ta tạo một danh sách chứa tất cả các prompt cần thiết.
        
        prompts_list = []
        for claim in claims:
            # Xác định prompt template sẽ sử dụng (logic này không đổi)
            prompt_template = self.prompt.qgen_prompt if prompt is None else prompt
            user_input = prompt_template.format(claim=claim)
            prompts_list.append(user_input)

        # Sử dụng hàm tiện ích của client để chuyển đổi danh sách các chuỗi prompt
        # thành một danh sách các "messages" theo đúng định dạng mà client yêu cầu.
        messages_list = self.llm_client.construct_message_list(prompts_list)
        
        # --- THAY ĐỔI 2: GỌI SONG SONG MỘT LẦN DUY NHẤT ---
        # Thay vì gọi `self.llm_client.call()` nhiều lần trong vòng lặp,
        # chúng ta gọi `self.llm_client.multi_call()` một lần duy nhất.
        # Hàm này sẽ xử lý việc gửi tất cả các yêu cầu đi song song.
        
        logger.info(f"Sending {len(claims)} query generation requests to LLM concurrently...")
        responses = self.llm_client.multi_call(
            messages_list=messages_list, 
            num_retries=generating_time
        )
        logger.info("Received all responses from LLM for query generation.")
        
        # --- THAY ĐỔI 3: XỬ LÝ KẾT QUẢ SAU KHI ĐÃ CÓ TẤT CẢ ---
        # `responses` là một danh sách các chuỗi JSON, có thứ tự tương ứng với `claims`.
        # Chúng ta dùng `zip` để duyệt qua cả hai danh sách này cùng lúc.
        
        for claim, response in zip(claims, responses):
            _questions = []
            try:
                # Logic để parse từng response không thay đổi.
                # Thêm kiểm tra `if response:` để xử lý trường hợp API trả về rỗng.
                if response:
                    cleaned_response = response.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = cleaned_response[7:-3].strip()
                    elif cleaned_response.startswith("```"):
                        cleaned_response = cleaned_response[3:-3].strip()
                    
                    response_dict = json.loads(cleaned_response)
                    
                    _questions = response_dict.get("Questions", [])
                    if not isinstance(_questions, list):
                        logger.warning(f"LLM returned non-list for Questions on claim '{claim[:50]}...'. Defaulting to empty list.")
                        _questions = []
                else:
                    logger.warning(f"Received an empty/failed response for claim '{claim[:50]}...'.")

            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Warning: LLM response parse fail for query generation on claim '{claim[:50]}...'. Error: {e}. Response was: '{response}'")

            # Gán kết quả vào dictionary, logic này không đổi.
            claim_query_dict[claim] = [claim] + _questions[:(self.max_query_per_claim - 1)]

        logger.info("Finished query generation.")
        return claim_query_dict