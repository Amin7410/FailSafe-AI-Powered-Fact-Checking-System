# ./factcheck/utils/llmclient/gemini_client.py

import google.generativeai as genai
import json
from .base import BaseClient
from factcheck.utils.logger import CustomLogger

import backoff
from google.api_core import exceptions

logger = CustomLogger(__name__).getlog()


def is_rate_limit_error(e):
    """Kiểm tra xem exception có phải là lỗi Rate Limit (429) không."""
    return isinstance(e, exceptions.ResourceExhausted)


class GeminiClient(BaseClient):
    def __init__(
        self,
        model: str = "gemini-2.5-flash",  # Nâng cấp lên 1.5-flash để có kết quả tốt hơn
        api_config: dict = None,
        max_requests_per_minute=8,
        request_window=60,
    ):
        super().__init__(model, api_config, max_requests_per_minute, request_window)

        if "GEMINI_API_KEY" not in self.api_config or not self.api_config["GEMINI_API_KEY"]:
            raise ValueError("GEMINI_API_KEY not found in api_config.")

        try:
            genai.configure(api_key=self.api_config["GEMINI_API_KEY"])
            # Cấu hình để bật JSON mode
            self.generation_config = genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
            self.client = genai.GenerativeModel(
                model_name=self.model,
                generation_config=self.generation_config
            )
            logger.info(f"GeminiClient initialized with model '{self.model}' in JSON mode.")
        except Exception as e:
            logger.error(f"Failed to initialize Google Generative AI client: {e}")
            raise

    @backoff.on_exception(
        backoff.expo,
        exceptions.ResourceExhausted,  # Chỉ retry khi gặp lỗi này
        max_tries=5,  # Thử lại tối đa 5 lần
        max_time=120  # Ngừng thử lại sau 120 giây
    )
    def _call(self, messages: list, **kwargs):
        try:
            full_prompt = "\n".join([msg['content'] for msg in messages])
            response = self.client.generate_content(full_prompt)
            
            if hasattr(response, 'usage_metadata'):
                self._log_usage(response.usage_metadata)
            
            # Thêm kiểm tra an toàn
            if not response.parts:
                logger.warning("Gemini returned an empty response (likely due to safety filters).")
                return "{}"

            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini client: {e}")
            return "{}"

    def get_request_length(self, messages):
        return 1

    def construct_message_list(
        self,
        prompt_list: list[str],
        # System role không được hỗ trợ trực tiếp như OpenAI, nên ta sẽ ghép nó vào prompt
        system_role: str = "You are a helpful assistant designed to output JSON.",
    ):
        messages_list = []
        for prompt in prompt_list:
            # Trong Gemini, ta thường kết hợp system role vào user prompt đầu tiên
            full_prompt_content = f"{system_role}\n\n{prompt}"
            messages = [
                {"role": "user", "content": full_prompt_content},
            ]
            messages_list.append(messages)
        return messages_list

    def _log_usage(self, usage_dict):
        try:
            self.usage.prompt_tokens += usage_dict.prompt_token_count
            self.usage.completion_tokens += usage_dict.candidates_token_count
        except Exception as e:
            logger.warning(f"Could not log token usage for Gemini: {e}")