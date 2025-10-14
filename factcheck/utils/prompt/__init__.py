# ./factcheck/utils/prompt/__init__.py

from .gemini_prompt import GEMINIPrompt
from .claude_prompt import ClaudePrompt
from .customized_prompt import CustomizedPrompt

prompt_map = {
    "chatgpt_prompt": GEMINIPrompt,
    "gemini_prompt": GEMINIPrompt,
    "claude_prompt": ClaudePrompt,
}


def prompt_mapper(prompt_name: str):
    if prompt_name in prompt_map:
        return prompt_map[prompt_name]()
    elif prompt_name.endswith("yaml") or prompt_name.endswith("json"):
        return CustomizedPrompt(prompt_name)
    else:
        raise NotImplementedError(f"Prompt {prompt_name} not implemented.")
