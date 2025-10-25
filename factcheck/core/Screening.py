# factcheck/core/Screening.py

import re
import sqlite3
import json
from factcheck.utils.logger import CustomLogger
import chromadb
import uuid
import math
from collections import Counter
import pickle
import numpy as np

logger = CustomLogger(__name__).getlog()
# Đường dẫn tới DB, tính từ thư mục gốc của dự án
SQLITE_DB_PATH = "data/sources.db" 


class MetadataAnalyzer:
    """
    Analyzes the source of the text based on domain names.
    It checks domains against a local SQLite DB and falls back to an LLM for unknown sources.
    """
    def __init__(self, llm_client=None):  # Truyền llm_client vào đây
        self.domain_regex = r'https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        self.llm_client = llm_client
        self.conn = None
        self.llm_cache = {}
        try:
            # `check_same_thread=False` quan trọng cho Flask khi dùng chung kết nối
            self.conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
            # Giúp truy cập cột bằng tên, ví dụ: result['bias']
            self.conn.row_factory = sqlite3.Row 
            logger.info(f"Successfully connected to sources DB at {SQLITE_DB_PATH}")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to SQLite DB: {e}. Analyzer will be degraded.")

    def _query_local_db(self, domain: str):
        """Truy vấn cơ sở dữ liệu cục bộ."""
        if not self.conn:
            return None
        cursor = self.conn.cursor()
        # Tối ưu logic tìm kiếm: tìm tên miền chính xác trước
        cursor.execute("SELECT * FROM sources WHERE domain = ?", (domain,))
        result = cursor.fetchone()
        if result:
            return dict(result)

        # Nếu không thấy, thử tìm tên miền cấp cao hơn (ví dụ: tìm 'nytimes.com' cho 'politics.nytimes.com')
        domain_parts = domain.split('.')
        if len(domain_parts) > 2:
            parent_domain = '.'.join(domain_parts[-2:])
            cursor.execute("SELECT * FROM sources WHERE domain = ?", (parent_domain,))
            result = cursor.fetchone()
            if result:
                return dict(result)
        return None

    def _evaluate_with_llm(self, domain: str):
        """Sử dụng LLM làm phương án dự phòng."""
        if not self.llm_client:
            logger.warning("LLM client not provided to MetadataAnalyzer. Cannot evaluate new domain.")
            return None

        logger.info(f"Domain '{domain}' not found in local DB. Querying LLM...")
        
        prompt = f"""
        Analyze the news website with the domain '{domain}'. 
        Provide your assessment in a strict JSON object with three keys:
        1. "name": The common name of the source.
        2. "bias": Political bias, choose one: "LEFT", "LEFT-CENTER", "CENTER", "RIGHT-CENTER", "RIGHT", "UNKNOWN".
        3. "credibility": Factual reporting credibility, choose one: "VERY HIGH", "HIGH", "MIXED", "LOW", "VERY LOW", "UNKNOWN".

        Your response must be only the JSON object, without any additional text or markdown formatting.
        """
        messages = self.llm_client.construct_message_list([prompt])
        try:
            response = self.llm_client.call(messages, num_retries=2)
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:-3].strip()
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:-3].strip()

            return json.loads(cleaned_response)
        except Exception as e:
            logger.error(f"Failed to get or parse LLM response for domain evaluation: {e}")
            return None
            
    def _map_credibility_to_trust_level(self, credibility: str):
        """Chuyển đổi nhãn của MBFC sang nhãn của hệ thống ('high', 'low', 'neutral')."""
        if not credibility: 
            return "neutral"
        
        credibility = credibility.upper()
        if credibility in ["VERY HIGH", "HIGH"]:
            return "high"
        elif credibility in ["LOW", "VERY LOW"]:
            return "low"
        else:  # MIXED, UNKNOWN, ...
            return "neutral"

    def analyze(self, text: str):
        """Phân tích văn bản, tìm tên miền và đánh giá."""
        domains = re.findall(self.domain_regex, text)
        if not domains:
            return {"trust_level": "unknown", "reason": "No domain found in text."}

        domain_to_check = domains[0]

        if domain_to_check in self.llm_cache:
            return self.llm_cache[domain_to_check]

        evaluation = self._query_local_db(domain_to_check)
        source_of_info = "Local DB"

        if not evaluation:
            evaluation = self._evaluate_with_llm(domain_to_check)
            source_of_info = "LLM Fallback"

        if not evaluation:
            return {"trust_level": "unknown", "reason": f"Could not evaluate domain '{domain_to_check}'."}
        
        trust_level = self._map_credibility_to_trust_level(evaluation.get('credibility'))
        reason = (f"Source: '{evaluation.get('name', domain_to_check)}'. "
                  f"Credibility: {evaluation.get('credibility', 'N/A')}. "
                  f"Bias: {evaluation.get('bias', 'N/A')}. "
                  f"(Evaluated by {source_of_info})")

        return {"trust_level": trust_level, "reason": reason}


class StylometryAnalyzer:
    """
    Analyzes the writing style of a text using a combination of rules and statistical models
    to detect sensationalism, propaganda, or low-quality content.
    """

    def __init__(self):
        """
        Initializes the analyzer with a set of sensational words and pre-calculated models.
        """
        # Giữ lại logic cũ
        self.sensational_words = {
            'shocking', 'amazing', 'unbelievable', 'secret', 'exposed', 'bombshell',
            'outrage', 'miracle', 'agenda', 'conspiracy', 'cover-up', 'hoax',
            'scandal', 'mind-blowing', 'must-see', 'breaking', 'urgent', 'warning'
        }
        
        # --- TÍCH HỢP THUẬT TOÁN MỚI ---
        self.idf_vectorizer = None
        self.entropy_stats = {"mean": 0, "std": 1}  # std=1 để tránh lỗi chia cho 0
        
        try:
            # Tải mô hình IDF đã tính toán trước
            with open('models/stylometry/idf_vector.pkl', 'rb') as f:
                self.idf_vectorizer = pickle.load(f)
            # Tải thông số entropy
            with open('models/stylometry/entropy_stats.json', 'r') as f:
                self.entropy_stats = json.load(f)
            logger.info("StylometryAnalyzer loaded with advanced models (IDF, Entropy).")
        except FileNotFoundError:
            logger.warning("Stylometry models not found. StylometryAnalyzer will run in basic mode.")

    def _calculate_entropy(self, text: str):
        """Tính Shannon Entropy của văn bản dựa trên phân phối từ."""
        tokens = re.findall(r'\b\w+\b', text.lower())
        if not tokens:
            return 0
        
        counts = Counter(tokens)
        total_tokens = len(tokens)
        probabilities = [count / total_tokens for count in counts.values()]
        
        # Thêm một giá trị rất nhỏ để tránh log(0)
        entropy = -sum(p * math.log2(p + 1e-12) for p in probabilities)
        return entropy

    def analyze(self, text: str):
        """
        Calculates a 'sensationalism score' based on multiple stylistic features.
        """
        if not text or not isinstance(text, str):
            return {"sensationalism_score": 0.0, "reason": "Input text is empty or invalid."}

        # --- 1. TÍNH TOÁN CÁC CHỈ SỐ CŨ ---
        num_alpha_chars = sum(1 for c in text if c.isalpha())
        if num_alpha_chars == 0:
            return {"sensationalism_score": 0.0, "reason": "No alphabetic characters to analyze."}
        
        num_uppers = sum(1 for c in text if c.isupper())
        upper_ratio = num_uppers / num_alpha_chars
        
        words = re.findall(r'\b\w+\b', text.lower())
        num_words = len(words)
        sensational_count = sum(1 for word in words if word in self.sensational_words)
        sensational_ratio = sensational_count / num_words if num_words > 0 else 0

        # --- 2. TÍNH TOÁN CÁC CHỈ SỐ MỚI ---
        entropy_score = 0
        keyword_abuse_score = 0
        
        # Chỉ chạy các thuật toán phức tạp nếu có mô hình và văn bản đủ dài
        if self.idf_vectorizer and num_words > 20:
            # Tính Entropy Score
            entropy_value = self._calculate_entropy(text)
            # Tính Z-score để xem entropy thấp đến mức nào so với chuẩn
            z_score = (entropy_value - self.entropy_stats['mean']) / self.entropy_stats['std']
            # Điểm số càng cao nếu entropy càng thấp (z-score càng âm)
            entropy_score = max(0, -z_score) 

            # Tính TF-IDF Score
            try:
                # Chuyển đổi văn bản thành vector TF-IDF
                tfidf_matrix = self.idf_vectorizer.transform([text])
                # Lấy điểm trung bình của 5 từ có TF-IDF cao nhất (đặc trưng nhất)
                # Điểm cao có thể cho thấy sự lạm dụng từ khóa
                top_tfidf_scores = np.sort(tfidf_matrix.toarray()[0])[-5:]
                keyword_abuse_score = np.mean(top_tfidf_scores)
            except Exception as e:
                logger.warning(f"Error calculating TF-IDF: {e}")
                keyword_abuse_score = 0

        # --- 3. TỔNG HỢP TẤT CẢ CÁC ĐIỂM ---
        # Trọng số có thể được tinh chỉnh sau này
        # Càng nhiều chỉ số, trọng số của các chỉ số cũ càng giảm để cân bằng
        final_score = (upper_ratio * 1.5) + \
                      (sensational_ratio * 3.0) + \
                      (entropy_score * 1.0) + \
                      (keyword_abuse_score * 0.35)  # TF-IDF có thể dao động lớn, nên trọng số thấp
        
        reason = (f"Sensational Words: {sensational_ratio:.2%}. "
                  f"Uppercase Ratio: {upper_ratio:.2%}. "
                  f"Repetitiveness (Low Entropy Score): {entropy_score:.2f}. "
                  f"Keyword Abuse Score: {keyword_abuse_score:.2f}.")
        
        return {"sensationalism_score": final_score, "reason": reason}
    

class ScreeningAdvisor:
    def __init__(self, db_path="./chroma_db", collection_name="screening_knowledge"):
        self.collection_name = collection_name
        self.collection = None
        try:
            client = chromadb.PersistentClient(path=db_path)
            self.collection = client.get_collection(name=self.collection_name)
            logger.info(f"ScreeningAdvisor connected to '{self.collection_name}' collection.")
        except Exception as e:
            # Lỗi này có thể xảy ra khi collection chưa tồn tại, không sao cả.
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