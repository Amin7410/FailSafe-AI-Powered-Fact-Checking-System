# ./factcheck/core/screening.py

import re
import os
from factcheck.utils.utils import load_yaml
from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()


class MetadataAnalyzer:
    """
    Analyzes the source of the text based on domain names found within it.
    It checks domains against a predefined list of high and low-trust sources.
    """

    def __init__(self, config_path='factcheck/config/domain_trust.yaml'):
        """
        Initializes the analyzer by loading the domain trust configuration.

        Args:
            config_path (str): The path to the YAML file containing trusted
                               and untrusted domain lists.
        """
        self.domain_regex = r'https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        try:
            self.config = load_yaml(config_path)
            logger.info(f"Successfully loaded domain trust config from {config_path}")
        except FileNotFoundError:
            logger.warning(f"Domain trust config file not found at {config_path}. Analyzer will be neutral.")
            self.config = {}
        except Exception as e:
            logger.error(f"Error loading domain trust config: {e}")
            self.config = {}

    def analyze(self, text: str):
        """
        Analyzes the input text to extract domains and determine their trust level.

        Args:
            text (str): The input text, which may contain URLs.

        Returns:
            dict: A dictionary containing the trust level ('high', 'low', 'neutral', 'unknown')
                  and a reason for the classification.
        """
        domains = re.findall(self.domain_regex, text)
        if not domains:
            return {"trust_level": "unknown", "reason": "No domain found in text."}

        # For simplicity, we analyze the first valid domain found.
        # A more advanced version could analyze all domains and aggregate the results.
        domain_to_check = domains[0]

        high_trust_list = self.config.get('high_trust', [])
        low_trust_list = self.config.get('low_trust', [])

        # Check if the found domain is a subdomain of any in the lists
        for trusted_domain in high_trust_list:
            if domain_to_check.endswith(trusted_domain):
                return {"trust_level": "high", "reason": f"Source '{domain_to_check}' is on the high-trust list."}

        for untrusted_domain in low_trust_list:
            if domain_to_check.endswith(untrusted_domain):
                return {"trust_level": "low", "reason": f"Source '{domain_to_check}' is on the low-trust list."}

        return {"trust_level": "neutral", "reason": f"Source '{domain_to_check}' is not on a predefined list."}


class StylometryAnalyzer:
    """
    Analyzes the writing style of a text to detect signs of sensationalism,
    propaganda, or low-quality content.
    """

    def __init__(self):
        """
        Initializes the analyzer with a set of sensational words.
        This list can be expanded or loaded from a config file.
        """
        self.sensational_words = {
            'shocking', 'amazing', 'unbelievable', 'secret', 'exposed', 'bombshell',
            'outrage', 'miracle', 'agenda', 'conspiracy', 'cover-up', 'hoax',
            'scandal', 'mind-blowing', 'must-see', 'breaking', 'urgent', 'warning'
        }

    def analyze(self, text: str):
        """
        Calculates a 'sensationalism score' based on stylistic features.

        The score is a weighted average of:
        - The ratio of uppercase characters.
        - The frequency of sensational words.

        Args:
            text (str): The input text to analyze.

        Returns:
            dict: A dictionary containing the sensationalism score (0 to 1+)
                  and a reason detailing the contributing factors.
        """
        if not text or not isinstance(text, str):
            return {"sensationalism_score": 0.0, "reason": "Input text is empty or invalid."}

        # 1. Calculate uppercase ratio
        num_chars = len(text)
        # Avoid counting spaces and numbers
        num_alpha_chars = sum(1 for c in text if c.isalpha())
        if num_alpha_chars == 0:
            return {"sensationalism_score": 0.0, "reason": "No alphabetic characters to analyze."}
            
        num_uppers = sum(1 for c in text if c.isupper())
        upper_ratio = num_uppers / num_alpha_chars

        # 2. Calculate sensational word frequency
        words = re.findall(r'\b\w+\b', text.lower())
        num_words = len(words)
        if num_words == 0:
            sensational_ratio = 0.0
        else:
            sensational_count = sum(1 for word in words if word in self.sensational_words)
            sensational_ratio = sensational_count / num_words

        # 3. Combine metrics into a single score (weights can be tuned)
        # We give sensational words a higher weight as they are a stronger indicator.
        score = (upper_ratio * 2.0) + (sensational_ratio * 5.0)  # Weights adjusted to make score more sensitive
        
        reason = (f"Uppercase Ratio: {upper_ratio:.2%} (contributes {upper_ratio * 2.0 :.2f} to score). "
                  f"Sensational Word Ratio: {sensational_ratio:.2%} (contributes {sensational_ratio * 5.0:.2f} to score).")
        
        return {"sensationalism_score": score, "reason": reason}
