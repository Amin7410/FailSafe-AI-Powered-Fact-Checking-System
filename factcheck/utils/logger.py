# ./factcheck/utils/logger.py

import os
import logging
from logging.handlers import RotatingFileHandler 


class CustomLogger:
    def __init__(self, name: str, loglevel=logging.INFO):
        self.logger = logging.getLogger("FactCheck")
        self.logger.setLevel(loglevel)
        
        if not os.path.exists("./log"):
            os.makedirs("./log")
            
        env = os.environ.get("env", "dev")
        filename = "./log/factcheck_{}.log".format(env)

        if not any(isinstance(h, RotatingFileHandler) for h in self.logger.handlers):
            try:
                fh = RotatingFileHandler(
                    filename=filename, 
                    maxBytes=5 * 1024 * 1024, 
                    backupCount=3,
                    encoding="utf-8"
                )
                fh.setLevel(loglevel)
                formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
                fh.setFormatter(formatter)
                self.logger.addHandler(fh)
            except PermissionError:
                pass

        if not any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers):
            ch = logging.StreamHandler()
            ch.setLevel(loglevel)
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def getlog(self):
        return self.logger