# factcheck/core/Screening.py (PHIÊN BẢN ĐÃ TỐI ƯU)

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
from urllib.parse import urlparse  
from factcheck.utils.config_loader import config

logger = CustomLogger(__name__).getlog()

SQLITE_DB_PATH = config.get('database.sqlite_path')


class MetadataAnalyzer:
    """
    [TỐI ƯU] Analyzes the source of the text based on domain names.
    It can now analyze a batch of domains in parallel to reduce latency.
    """
    def __init__(self, llm_client=None):
        # self.domain_regex = r'https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})' # Regex cũ
        self.llm_client = llm_client
        self.conn = None
        self.llm_cache = {}  # Cache để tránh gọi lại API trong cùng một request
        try:
            self.conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row 
            logger.info(f"Successfully connected to sources DB at {SQLITE_DB_PATH}")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to SQLite DB: {e}. Analyzer will be degraded.")

    def _get_domain_from_url(self, url: str) -> str | None:
        """Trích xuất domain chính từ một URL đầy đủ."""
        try:
            # urlparse sẽ tách URL thành các thành phần
            parsed_url = urlparse(url)
            # Lấy netloc (ví dụ: 'www.nytimes.com') và loại bỏ 'www.' nếu có
            domain = parsed_url.netloc.replace('www.', '')
            return domain if domain else None
        except Exception:
            return None

    def _query_local_db(self, domain: str):
        """Truy vấn cơ sở dữ liệu cục bộ."""
        if not self.conn or not domain:
            return None
        cursor = self.conn.cursor()
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
        return None

    # === HÀM ĐƯỢC NÂNG CẤP ĐỂ XỬ LÝ BATCH ===
    def _evaluate_domains_with_llm(self, domains: list[str]) -> dict:
        """Sử dụng LLM để đánh giá một danh sách các domain song song."""
        if not self.llm_client or not domains:
            return {}

        logger.info(f"Querying LLM in parallel for {len(domains)} unknown domains...")
        
        # Tạo prompt cho từng domain
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
        
        # Gửi tất cả các yêu cầu đi song song
        messages_list = self.llm_client.construct_message_list(prompts)
        responses = self.llm_client.multi_call(messages_list, num_retries=2)
        
        # Xử lý kết quả trả về
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
                    self.llm_cache[domain] = eval_result  # Cập nhật cache
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

    # === HÀM MỚI ĐỂ ĐIỀU PHỐI XỬ LÝ BATCH ===
    def analyze_batch(self, urls: list[str]) -> dict[str, dict]:
        """
        Phân tích một danh sách các URL, tối ưu hóa việc truy vấn DB và LLM.
        Returns a dictionary mapping each URL to its trust information.
        """
        domains_to_find = {url: self._get_domain_from_url(url) for url in urls if url}
        unique_domains = set(filter(None, domains_to_find.values()))
        
        domain_evaluations = {}
        domains_for_llm = []

        # 1. Kiểm tra cache và DB cho tất cả các domain
        for domain in unique_domains:
            if domain in self.llm_cache:
                domain_evaluations[domain] = self.llm_cache[domain]
                continue
            
            db_result = self._query_local_db(domain)
            if db_result:
                domain_evaluations[domain] = db_result
            else:
                domains_for_llm.append(domain)
        
        # 2. Gọi LLM một lần duy nhất cho tất cả các domain chưa biết
        if domains_for_llm:
            llm_results = self._evaluate_domains_with_llm(domains_for_llm)
            domain_evaluations.update(llm_results)
            
        # 3. Tạo kết quả cuối cùng cho từng URL
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

    # Giữ lại hàm cũ để tương thích, nhưng nó sẽ kém hiệu quả hơn
    def analyze(self, text: str):
        """Phân tích văn bản, tìm URL và đánh giá."""
        # Sử dụng regex để tìm URL thay vì domain
        urls = re.findall(r'https?://[^\s/$.?#].[^\s]*', text)
        if not urls:
            return {"trust_level": "unknown", "reason": "No URL found in text."}
        
        # Chỉ phân tích URL đầu tiên
        first_url = urls[0]
        result = self.analyze_batch([first_url])
        return result.get(first_url, {"trust_level": "unknown", "reason": "Analysis failed."})


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
    def __init__(self, db_path=None, collection_name=None):
        if db_path is None:
            db_path = config.get('database.chroma_path')
        if collection_name is None:
            collection_name = config.get('vectordb.screening_collection_name')
        
        self.collection_name = collection_name
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