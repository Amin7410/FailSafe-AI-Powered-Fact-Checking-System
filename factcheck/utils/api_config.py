# ./factcheck/utils/api_config.py

import os

keys = [
    "SERPER_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "LOCAL_API_KEY",
    "LOCAL_API_URL",
    "GEMINI_API_KEY",
    "GEMINI_API_KEYS",
]


def load_api_config(api_config: dict = None):
    if api_config is None:
        api_config = dict()
    assert type(api_config) is dict, "api_config must be a dictionary."

    merged_config = {}

    for key in keys:
        merged_config[key] = api_config.get(key, None)
        if merged_config[key] is None:
            merged_config[key] = os.environ.get(key, None)

    if merged_config.get("GEMINI_API_KEYS"):
        raw_keys = merged_config["GEMINI_API_KEYS"]
        if isinstance(raw_keys, str):
            key_list = [k.strip() for k in raw_keys.split(',') if k.strip()]
            merged_config["GEMINI_KEY_POOL"] = key_list
        elif isinstance(raw_keys, list):
            merged_config["GEMINI_KEY_POOL"] = raw_keys
    elif merged_config.get("GEMINI_API_KEY"):
        merged_config["GEMINI_KEY_POOL"] = [merged_config["GEMINI_API_KEY"]]
    else:
        merged_config["GEMINI_KEY_POOL"] = []

    for key in api_config.keys():
        if key not in keys:
            merged_config[key] = api_config[key]
            
    return merged_config