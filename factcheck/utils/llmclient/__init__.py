# ./factcheck/utils/llmclient/__init__.py

from .gpt_client import GPTClient
from .claude_client import ClaudeClient
from .local_openai_client import LocalOpenAIClient
from .gemini_client import GeminiClient

CLIENTS = {
    "gpt": GPTClient,
    "claude": ClaudeClient,
    "local_openai": LocalOpenAIClient,
    "gemini": GeminiClient,
}


def model2client(model_name: str):
    if model_name.startswith("gpt"):
        return GPTClient
    elif model_name.startswith("claude"):
        return ClaudeClient
    elif model_name.startswith("vicuna"):
        return LocalOpenAIClient
    elif model_name.startswith("gemini"):
        return GeminiClient
    else:
        raise ValueError(f"Model {model_name} not supported.")
