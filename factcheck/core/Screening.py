# factcheck/core/Screening.py 

import re
import sqlite3
import json
from factcheck.utils.logger import CustomLogger
import chromadb
import uuid
import math
from factcheck.utils.database import DatabaseProvider
from collections import Counter
import pickle
import numpy as np
from urllib.parse import urlparse
from factcheck.utils.config_loader import config, PROJECT_ROOT 

logger = CustomLogger(__name__).getlog()

SQLITE_DB_PATH = str(PROJECT_ROOT / config.get('database.sqlite_path', 'data/sources.db'))


class MetadataAnalyzer:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.conn = None
        self.llm_cache = {}

    def _get_domain_from_url(self, url: str) -> str | None:
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace('www.', '')
            return domain if domain else None
        except Exception:
            return None

    def _query_local_db(self, domain: str):
        if not self.conn or not domain:
            return None
        try:
            conn = DatabaseProvider.get_sqlite_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM sources WHERE domain = ?", (domain,))
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            domain_parts = domain.split('.')
            if len(domain_parts) > 2:
                parent_domain = '.'.join(domain_parts[-2:])
                cursor.execute("SELECT * FROM sources WHERE domain = ?", (parent_domain,))
                result = cursor.fetchone()
                if result:
                    return dict(result)
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error querying local DB: {e}")
            return None

    def _evaluate_domains_with_llm(self, domains: list[str]) -> dict:
        """Sử dụng LLM để đánh giá một danh sách các domain song song."""
        if not self.llm_client or not domains:
            return {}

        logger.info(f"Querying LLM in parallel for {len(domains)} unknown domains...")
        
        prompts = []
        for domain in domains:
            prompt = f"""
            Analyze the news website with the domain '{domain}'. 
            Provide your assessment in a strict JSON object with three keys:
            1. "name": The common name of the source.
            2. "bias": Political bias, choose one: "LEFT", "LEFT-CENTER", "CENTER", "RIGHT-CENTER", "RIGHT", "UNKNOWN".
            3. "credibility": Factual reporting credibility, choose one: "VERY HIGH", "HIGH", "MIXED", "LOW", "VERY LOW", "UNKNOWN".
            Your response must be only the JSON object, without any additional text or markdown formatting.
            """
            prompts.append(prompt)
        
        messages_list = self.llm_client.construct_message_list(prompts)
        responses = self.llm_client.multi_call(messages_list, num_retries=2)
        
        evaluations = {}
        for domain, response in zip(domains, responses):
            try:
                if response:
                    cleaned_response = response.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = cleaned_response[7:-3].strip()
                    elif cleaned_response.startswith("```"):
                        cleaned_response = cleaned_response[3:-3].strip()
                    eval_result = json.loads(cleaned_response)
                    evaluations[domain] = eval_result
                    self.llm_cache[domain] = eval_result
            except Exception as e:
                logger.error(f"Failed to parse LLM response for domain '{domain}': {e}")
        
        return evaluations
            
    def _map_credibility_to_trust_level(self, credibility: str):
        if not credibility: 
            return "neutral"
        
        credibility = credibility.upper()
        if credibility in ["VERY HIGH", "HIGH"]:
            return "high"
        elif credibility in ["LOW", "VERY LOW"]:
            return "low"
        else:
            return "neutral"

    def analyze_batch(self, urls: list[str]) -> dict[str, dict]:
        domains_to_find = {url: self._get_domain_from_url(url) for url in urls if url}
        unique_domains = set(filter(None, domains_to_find.values()))
        
        domain_evaluations = {}
        domains_for_llm = []

        for domain in unique_domains:
            if domain in self.llm_cache:
                domain_evaluations[domain] = self.llm_cache[domain]
                continue
            
            db_result = self._query_local_db(domain)
            if db_result:
                domain_evaluations[domain] = db_result
            else:
                domains_for_llm.append(domain)
        
        if domains_for_llm:
            llm_results = self._evaluate_domains_with_llm(domains_for_llm)
            domain_evaluations.update(llm_results)
         
        final_results = {}
        for url, domain in domains_to_find.items():
            if not domain or domain not in domain_evaluations:
                final_results[url] = {"trust_level": "unknown", "reason": f"Could not evaluate domain for URL: {url}"}
                continue

            evaluation = domain_evaluations[domain]
            trust_level = self._map_credibility_to_trust_level(evaluation.get('credibility'))
            reason = (f"Source: '{evaluation.get('name', domain)}'. "
                      f"Credibility: {evaluation.get('credibility', 'N/A')}. "
                      f"Bias: {evaluation.get('bias', 'N/A')}.")
            final_results[url] = {"trust_level": trust_level, "reason": reason}
            
        return final_results

    def analyze(self, text: str):
        urls = re.findall(r'https?://[^\s/$.?#].[^\s]*', text)
        if not urls:
            return {"trust_level": "unknown", "reason": "No URL found in text."}
        first_url = urls[0]
        result = self.analyze_batch([first_url])
        return result.get(first_url, {"trust_level": "unknown", "reason": "Analysis failed."})


class StylometryAnalyzer:
    def __init__(self):
        self.sensational_words = {
            'shocking', 'amazing', 'unbelievable', 'secret', 'exposed', 'bombshell',
            'outrage', 'miracle', 'agenda', 'conspiracy', 'cover-up', 'hoax',
            'scandal', 'mind-blowing', 'must-see', 'breaking', 'urgent', 'warning'
        }
        
        self.idf_vectorizer = None
        self.entropy_stats = {"mean": 0, "std": 1}
        
        idf_path = PROJECT_ROOT / 'models/stylometry/idf_vector.pkl'
        stats_path = PROJECT_ROOT / 'models/stylometry/entropy_stats.json'
        
        try:
            with open(idf_path, 'rb') as f:
                self.idf_vectorizer = pickle.load(f)
            with open(stats_path, 'r') as f:
                self.entropy_stats = json.load(f)
            logger.info("StylometryAnalyzer loaded models successfully.")
        except FileNotFoundError:
            logger.warning(f"Stylometry models not found at {idf_path}. Running basic mode.")

    def _calculate_entropy(self, text: str):
        """Tính Shannon Entropy của văn bản dựa trên phân phối từ."""
        tokens = re.findall(r'\b\w+\b', text.lower())
        if not tokens:
            return 0
        
        counts = Counter(tokens)
        total_tokens = len(tokens)
        probabilities = [count / total_tokens for count in counts.values()]

        entropy = -sum(p * math.log2(p + 1e-12) for p in probabilities)
        return entropy

    def analyze(self, text: str):
        """
        Calculates a 'sensationalism score' based on multiple stylistic features.
        """
        if not text or not isinstance(text, str):
            return {"sensationalism_score": 0.0, "reason": "Input text is empty or invalid."}

        num_alpha_chars = sum(1 for c in text if c.isalpha())
        if num_alpha_chars == 0:
            return {"sensationalism_score": 0.0, "reason": "No alphabetic characters to analyze."}
        
        num_uppers = sum(1 for c in text if c.isupper())
        upper_ratio = num_uppers / num_alpha_chars
        
        words = re.findall(r'\b\w+\b', text.lower())
        num_words = len(words)
        sensational_count = sum(1 for word in words if word in self.sensational_words)
        sensational_ratio = sensational_count / num_words if num_words > 0 else 0

        entropy_score = 0
        keyword_abuse_score = 0
        
        if self.idf_vectorizer and num_words > 20:
            entropy_value = self._calculate_entropy(text)

            z_score = (entropy_value - self.entropy_stats['mean']) / self.entropy_stats['std']

            entropy_score = max(0, -z_score) 

            try:
                tfidf_matrix = self.idf_vectorizer.transform([text])
                top_tfidf_scores = np.sort(tfidf_matrix.toarray()[0])[-5:]
                keyword_abuse_score = np.mean(top_tfidf_scores)
            except Exception as e:
                logger.warning(f"Error calculating TF-IDF: {e}")
                keyword_abuse_score = 0
        final_score = (upper_ratio * 1.5) + \
                      (sensational_ratio * 3.0) + \
                      (entropy_score * 1.0) + \
                      (keyword_abuse_score * 0.35) 
        reason = (f"Sensational Words: {sensational_ratio:.2%}. "
                  f"Uppercase Ratio: {upper_ratio:.2%}. "
                  f"Repetitiveness (Low Entropy Score): {entropy_score:.2f}. "
                  f"Keyword Abuse Score: {keyword_abuse_score:.2f}.")
        return {"sensationalism_score": final_score, "reason": reason}


class ScreeningAdvisor:
    def __init__(self, db_path=None, collection_name=None):
        if db_path is None:
            db_path = config.get('database.chroma_path')
        if collection_name is None:
            collection_name = config.get('vectordb.screening_collection_name')
        
        self.collection = None

        self.collection_name = collection_name
        try:
            client = chromadb.PersistentClient(path=db_path)
            self.collection = client.get_collection(name=self.collection_name)
            logger.info(f"ScreeningAdvisor connected to '{self.collection_name}' collection.")
        except Exception as e:
            logger.warning(f"ScreeningAdvisor could not connect to ChromaDB collection '{collection_name}': {e}. Advisor will be inactive until collection is created.")

    def learn_from_result(self, text: str, final_output: dict):
        if not self.collection:
            return

        summary = final_output.get('summary', {})
        claim_details = final_output.get('claim_detail', [])
        status = summary.get('status')
        num_claims = summary.get('num_claims', 0)
        num_checkworthy_claims = summary.get('num_checkworthy_claims', 0)
        suggested_label = 'unknown'

        if status == "SCREENED_OUT":
            message = summary.get('factuality', '')
            if 'opinion' in message:
                suggested_label = 'opinion'
            elif 'question' in message:
                suggested_label = 'question'
        elif num_claims > 0 and num_checkworthy_claims == 0:
            suggested_label = 'opinion'
        elif num_claims == 0:
            suggested_label = 'no_claims'
        elif num_claims > 0:
            is_opinion = True
            for claim in claim_details:
                if claim['factuality'] != "Nothing to check.":
                    evidences = claim.get('evidences', [])
                    if not evidences:
                        continue
                    all_irrelevant = all(evi.get('relationship') == 'IRRELEVANT' for evi in evidences)
                    if not all_irrelevant:
                        is_opinion = False
                        break
            if is_opinion:
                suggested_label = 'opinion'
            else:
                suggested_label = 'verifiable'
        
        if suggested_label == 'unknown':
            return

        try:
            unique_id = str(uuid.uuid4())
            self.collection.add(
                documents=[text],
                metadatas=[{"label": suggested_label}],
                ids=[unique_id]
            )
            logger.info(f"Learned a new lesson. Label: '{suggested_label}', Text: '{text[:50]}...'")
        except Exception as e:
            logger.error(f"Failed to save a lesson to ScreeningKnowledgeDB: {e}")

    def get_advice(self, text: str, n_results: int = 3, threshold: float = 0.5) -> str:
        if not self.collection or self.collection.count() == 0:
            return 'no_knowledge'

        try:
            results = self.collection.query(
                query_texts=[text],
                n_results=n_results,
                include=["metadatas", "distances"]
            )
            
            if not results or not results['ids'][0]:
                return 'no_match'

            distances = results['distances'][0]
            metadatas = results['metadatas'][0]
            
            confident_results = [
                metadatas[i]['label'] for i, dist in enumerate(distances) if dist < threshold
            ]
            
            if not confident_results:
                return 'too_dissimilar'

            advice = max(set(confident_results), key=confident_results.count)
            return advice

        except Exception as e:
            logger.error(f"Failed to get advice from ScreeningKnowledgeDB: {e}")
            return 'db_error'