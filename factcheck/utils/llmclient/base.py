# ./factcheck/utils/llmclient/base.py

import time
import asyncio
import json
import logging
from abc import abstractmethod
from functools import partial, lru_cache
from collections import deque

from ..data_class import TokenUsage

logger = logging.getLogger(__name__)


class BaseClient:
    def __init__(
        self,
        model: str,
        api_config: dict,
        max_requests_per_minute: int,
        request_window: int,
    ) -> None:
        self.model = model
        self.api_config = api_config
        self.max_requests_per_minute = max_requests_per_minute
        self.request_window = request_window
        self.traffic_queue = deque()
        self.total_traffic = 0
        self.usage = TokenUsage(model=model)

    @staticmethod
    def _make_hashable(data):
        return json.dumps(data, sort_keys=True)

    @lru_cache(maxsize=256)
    def _cached_call_wrapper(self, messages_hashable: str, **kwargs):
        messages = json.loads(messages_hashable)
        return self._call(messages, **kwargs)

    @abstractmethod
    def _call(self, messages: list, **kwargs):
        pass
    
    @abstractmethod
    def _log_usage(self, usage_dict):
        pass

    def get_usage(self):
        return self.usage

    def reset_usage(self):
        self.usage.prompt_tokens = 0
        self.usage.completion_tokens = 0

    @abstractmethod
    def construct_message_list(self, prompt_list: list[str]) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def get_request_length(self, messages):
        raise NotImplementedError

    def call(self, messages: list[str], num_retries=3, waiting_time=1, **kwargs):
        seed = kwargs.get("seed", 42)
        assert type(seed) is int, "Seed must be an integer."
        assert len(messages) == 1, "Only one message is allowed for this function."

        hashable_messages = self._make_hashable(messages[0])
        
        r = ""
        for _ in range(num_retries):
            try:
                r = self._cached_call_wrapper(hashable_messages, seed=seed)
                if r:
                    break
            except Exception as e:
                print(f"Error LLM Client call: {e} Retrying...")
                self._cached_call_wrapper.cache_clear() 
                time.sleep(waiting_time)

        if r == "":
            raise ValueError("Failed to get response from LLM Client.")
        return r

    def set_model(self, model: str):
        self.model = model

    async def _async_call(self, messages: list, **kwargs):
        while True:  
            self._expire_old_traffic()
            
            if len(self.traffic_queue) < self.max_requests_per_minute:
                break 
          
            oldest_request_time = self.traffic_queue[0][0]
            time_to_wait = (oldest_request_time + self.request_window) - time.time()

            wait_duration = max(0, time_to_wait) + 0.1
            logger.debug(f"Rate limit reached. Waiting for {wait_duration:.2f} seconds...")
            await asyncio.sleep(wait_duration)

        loop = asyncio.get_running_loop()
        hashable_messages = self._make_hashable(messages)
        
        self.traffic_queue.append((time.time(), self.get_request_length(messages)))
        self.total_traffic += self.get_request_length(messages)
        
        response = await loop.run_in_executor(None, partial(self._cached_call_wrapper, hashable_messages, **kwargs))

        return response

    def multi_call(self, messages_list, **kwargs):
        tasks = [self._async_call(messages=messages, **kwargs) for messages in messages_list]
        asyncio.set_event_loop(asyncio.SelectorEventLoop())
        loop = asyncio.get_event_loop()
        responses = loop.run_until_complete(asyncio.gather(*tasks))
        return responses

    def _expire_old_traffic(self):
        current_time = time.time()
        while self.traffic_queue and self.traffic_queue[0][0] + self.request_window < current_time:
            self.total_traffic -= self.traffic_queue.popleft()[1]