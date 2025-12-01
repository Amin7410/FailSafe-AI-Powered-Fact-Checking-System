# ./factcheck/utils/llmclient/gemini_client.py

import google.generativeai as genai
import threading
from itertools import cycle
from .base import BaseClient
from factcheck.utils.logger import CustomLogger
import backoff
from google.api_core import exceptions
from google.ai.generativelanguage_v1beta.types import content

logger = CustomLogger(__name__).getlog()

VERIFICATION_SCHEMA = content.Schema(
    type=content.Type.OBJECT,
    properties={
        "verifications": content.Schema(
            type=content.Type.ARRAY,
            items=content.Schema(
                type=content.Type.OBJECT,
                properties={
                    "id": content.Schema(type=content.Type.STRING),
                    "reasoning": content.Schema(type=content.Type.STRING),
                    "relationship": content.Schema(
                        type=content.Type.STRING,
                        enum=["SUPPORTS", "REFUTES", "IRRELEVANT"] 
                    ),
                },
                required=["id", "reasoning", "relationship"],
            ),
        ),
    },
    required=["verifications"],
)
SCHEMA_MAP = {
    "verification": VERIFICATION_SCHEMA
}


class GeminiClient(BaseClient):
    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        api_config: dict = None,
        max_requests_per_minute=40, 
        request_window=60,
    ):
        super().__init__(model, api_config, max_requests_per_minute, request_window)

        if "GEMINI_KEY_POOL" in self.api_config and self.api_config["GEMINI_KEY_POOL"]:
            self.key_pool = self.api_config["GEMINI_KEY_POOL"]
        elif "GEMINI_API_KEY" in self.api_config and self.api_config["GEMINI_API_KEY"]:
            self.key_pool = [self.api_config["GEMINI_API_KEY"]]
        else:
            raise ValueError("No GEMINI_API_KEYS found in configuration.")

        logger.info(f"GeminiClient initialized with {len(self.key_pool)} API keys available.")
        
        self.key_cycle = cycle(self.key_pool)
        
        self.config_lock = threading.Lock()

        self.default_generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )

    def _get_next_key(self):
        return next(self.key_cycle)

    @backoff.on_exception(
        backoff.expo,
        exceptions.ResourceExhausted, 
        max_tries=5,
        max_time=120
    )
    def _call(self, messages: list, **kwargs):
        current_key = self._get_next_key()
        
        schema_type = kwargs.get("schema_type")
        
        if schema_type and schema_type in SCHEMA_MAP:
            gen_config = genai.types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=SCHEMA_MAP[schema_type]
            )
        else:
            gen_config = self.default_generation_config

        try:
            full_prompt = "\n".join([msg['content'] for msg in messages])
            
            response = None
            with self.config_lock:
                genai.configure(api_key=current_key)
                model_instance = genai.GenerativeModel(
                    model_name=self.model,
                    generation_config=gen_config 
                )
                response = model_instance.generate_content(full_prompt)

            if hasattr(response, 'usage_metadata'):
                self._log_usage(response.usage_metadata)
            
            if not response.parts:
                logger.warning(f"Gemini (Key ...{current_key[-4:]}) returned empty response.")
                return "{}"

            return response.text

        except Exception as e:
            logger.error(f"Error calling Gemini with key ...{current_key[-4:]}: {e}")
            raise e 

    def get_request_length(self, messages):
        return 1

    def construct_message_list(
        self,
        prompt_list: list[str],
        system_role: str = "You are a helpful assistant designed to output JSON.",
    ):
        messages_list = []
        for prompt in prompt_list:
            full_prompt_content = f"{system_role}\n\n{prompt}"
            messages = [{"role": "user", "content": full_prompt_content}]
            messages_list.append(messages)
        return messages_list

    def _log_usage(self, usage_dict):
        try:
            self.usage.prompt_tokens += usage_dict.prompt_token_count
            self.usage.completion_tokens += usage_dict.candidates_token_count
        except Exception:
            pass