# factcheck/utils/config_loader.py

import yaml
from pathlib import Path


class ConfigLoader:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = 'config.yaml'):
        if not hasattr(self, 'initialized'):
            # Lấy đường dẫn tuyệt đối đến thư mục gốc của dự án
            project_root = Path(__file__).resolve().parent.parent.parent
            self.config_file = project_root / config_path
            
            try:
                with open(self.config_file, 'r') as f:
                    self.data = yaml.safe_load(f)
                self.initialized = True
            except FileNotFoundError:
                raise FileNotFoundError(f"Config file not found at: {self.config_file}")
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error parsing YAML file: {e}")

    def get(self, key_path: str, default=None):
        """
        Lấy giá trị từ cấu hình bằng cách sử dụng chuỗi key có dấu chấm.
        Ví dụ: 'database.sqlite_path'
        """
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

# Tạo một instance duy nhất (singleton) để toàn bộ ứng dụng có thể import và sử dụng


config = ConfigLoader()