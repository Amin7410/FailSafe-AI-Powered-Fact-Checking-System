# scripts/build_stylometry_corpus.py

import os
import re
import json
import pickle
import math
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# Cài đặt thư viện datasets nếu chưa có
try:
    from datasets import load_dataset
except ImportError:
    print("Thư viện 'datasets' chưa được cài đặt. Vui lòng chạy: pip install datasets")
    exit()

# Thư mục để lưu các mô hình đã xử lý
MODEL_DIR = "models/stylometry"
IDF_VECTOR_PATH = os.path.join(MODEL_DIR, "idf_vector.pkl")
ENTROPY_STATS_PATH = os.path.join(MODEL_DIR, "entropy_stats.json")


def calculate_entropy(text: str):
    """Tính Shannon Entropy của văn bản dựa trên phân phối từ."""
    tokens = re.findall(r'\b\w+\b', text.lower())
    if not tokens:
        return 0
    
    counts = Counter(tokens)
    total_tokens = len(tokens)
    probabilities = [count / total_tokens for count in counts.values()]
    
    entropy = -sum(p * math.log2(p) for p in probabilities)
    return entropy


def main():
    """
    Hàm chính để tải dữ liệu, tính toán IDF và entropy, sau đó lưu lại.
    """
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    print("Đang tải bộ dữ liệu văn bản chuẩn (ag_news)...")
    # Sử dụng ag_news, một bộ dữ liệu tin tức phổ biến, làm kho văn bản "bình thường"
    # Lấy 10,000 mẫu để tính toán cho nhanh
    try:
        dataset = load_dataset("ag_news", split="train[:10000]")
        corpus = dataset['text']
        print(f"Đã tải thành công {len(corpus)} bài báo.")
    except Exception as e:
        print(f"Lỗi khi tải dataset: {e}")
        print("Vui lòng kiểm tra kết nối mạng và thử lại.")
        return

    # --- 1. Tính toán và lưu mô hình IDF ---
    print("\nĐang tính toán mô hình IDF từ kho văn bản...")
    # chỉ sử dụng idf, không sử dụng tf. max_features giới hạn số từ để mô hình nhẹ hơn.
    vectorizer = TfidfVectorizer(max_features=20000, use_idf=True, smooth_idf=True, norm=None)
    vectorizer.fit(corpus)
    
    # Chúng ta không cần toàn bộ vectorizer, chỉ cần phần idf_
    # Nhưng để đơn giản, ta lưu cả object và chỉ dùng nó để transform sau này
    with open(IDF_VECTOR_PATH, 'wb') as f:
        pickle.dump(vectorizer, f)
    print(f"Đã lưu mô hình IDF vào: {IDF_VECTOR_PATH}")

    # --- 2. Tính toán và lưu thông số Entropy ---
    print("\nĐang tính toán thông số Entropy từ kho văn bản...")
    entropy_values = [calculate_entropy(text) for text in corpus]
    
    mean_entropy = np.mean(entropy_values)
    std_entropy = np.std(entropy_values)
    
    entropy_stats = {
        "mean": mean_entropy,
        "std": std_entropy
    }
    
    with open(ENTROPY_STATS_PATH, 'w') as f:
        json.dump(entropy_stats, f, indent=2)
    
    print(f"Đã lưu thông số Entropy vào: {ENTROPY_STATS_PATH}")
    print("\n--- Phân tích Entropy mẫu ---")
    print(f"Entropy trung bình của văn bản tin tức chuẩn: {mean_entropy:.4f}")
    print(f"Độ lệch chuẩn của Entropy: {std_entropy:.4f}")
    print("\nHoàn tất! Các mô hình cho StylometryAnalyzer đã sẵn sàng.")


if __name__ == "__main__":
    main()