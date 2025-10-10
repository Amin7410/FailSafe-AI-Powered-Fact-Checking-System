from langchain_google_genai import ChatGoogleGenerativeAI
from .base import BaseClient
import logging

logger = logging.getLogger(__name__)

class GeminiClient(BaseClient):
    def __init__(
        self,
        model: str = "gemini-2.5-flash",  # Sử dụng tên model sạch, không cần "models/"
        api_config: dict = None,
        max_requests_per_minute=60,
        request_window=60,
    ):
        super().__init__(model, api_config, max_requests_per_minute, request_window)

        # Kiểm tra API key
        if "GEMINI_API_KEY" not in self.api_config or not self.api_config["GEMINI_API_KEY"]:
            raise ValueError("GEMINI_API_KEY not found in api_config. Please check your config file.")

        # Khởi tạo client của LangChain, truyền API key vào trực tiếp
        # LangChain sẽ tự động xử lý tất cả các vấn đề về endpoint và phiên bản API
        try:
            self.langchain_client = ChatGoogleGenerativeAI(
                model=self.model,
                google_api_key=self.api_config["GEMINI_API_KEY"],
                convert_system_message_to_human=True # Giúp tương thích tốt hơn
            )
        except Exception as e:
            logger.error(f"Failed to initialize LangChain ChatGoogleGenerativeAI: {e}")
            raise

    def _call(self, messages: list, **kwargs):
        try:
            # LangChain's invoke method xử lý các định dạng message khác nhau
            response = self.langchain_client.invoke(messages)
            
            # Ghi lại token usage từ metadata của LangChain
            if hasattr(response, 'usage_metadata'):
                self._log_usage(response.usage_metadata)

            return response.content
        except Exception as e:
            logger.error(f"Error calling LangChain Gemini client: {e}")
            return ""

    def get_request_length(self, messages):
        return 1

    def construct_message_list(
        self,
        prompt_list: list[str],
        system_role: str = "You are a helpful assistant designed to output JSON.",
    ):
        # Tạo định dạng message mà LangChain hiểu rõ
        messages_list = []
        for prompt in prompt_list:
            messages = [
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt},
            ]
            messages_list.append(messages)
        return messages_list

    def _log_usage(self, usage_dict):
        try:
            self.usage.prompt_tokens += usage_dict.get('prompt_token_count', 0)
            self.usage.completion_tokens += usage_dict.get('candidates_token_count', 0)
        except Exception as e:
            logger.warning(f"Could not log token usage for LangChain Gemini: {e}")