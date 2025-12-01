# factcheck/utils/config_loader.py

import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class ConfigLoader:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = 'config.yaml'):
        if not hasattr(self, 'initialized'):
            self.config_file = PROJECT_ROOT / config_path
            try:
                with open(self.config_file, 'r') as f:
                    self.data = yaml.safe_load(f)
                self.initialized = True
            except FileNotFoundError:
                raise FileNotFoundError(f"Config file not found at: {self.config_file}")
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error parsing YAML file: {e}")

    def get(self, key_path: str, default=None):
        keys = key_path.split('.')
        value = self.data
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            if default is not None:
                return default
            raise KeyError(f"Config key '{key_path}' not found in {self.config_file}")


config = ConfigLoader()