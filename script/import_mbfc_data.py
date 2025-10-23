# scripts/import_mbfc_data.py

import sqlite3
import json
import re
from urllib.parse import urlparse
import os

try:
    from datasets import load_dataset
except ImportError:
    print("Thư viện 'datasets' chưa được cài đặt. Vui lòng chạy: pip install datasets")
    exit()

# Đường dẫn cần cấu hình
DATA_DIR = "data"
MBFC_JSON_PATH = os.path.join(DATA_DIR, "mbfc_huggingface_data.json")
SQLITE_DB_PATH = os.path.join(DATA_DIR, "sources.db")

def download_mbfc_dataset():
    """Tải dataset từ Hugging Face và lưu cục bộ."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    print("Downloading/loading MBFC dataset from Hugging Face (zainmujahid/mbfc-media-outlets)...")
    try:
        dataset = load_dataset("zainmujahid/mbfc-media-outlets", split="train")
        with open(MBFC_JSON_PATH, 'w', encoding='utf-8') as f:
            for record in dataset:
                f.write(json.dumps(record) + '\n')
        print(f"Successfully saved dataset to {MBFC_JSON_PATH}")
        return True
    except Exception as e:
        print(f"FATAL ERROR: Could not download dataset from Hugging Face: {e}")
        return False

# =========================================================
# SỬA LỖI Ở ĐÂY: Truyền 'conn' vào hàm
# =========================================================
def setup_database(conn):
    """Tạo bảng trong DB SQLite."""
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS sources')
    cursor.execute('''
        CREATE TABLE sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE NOT NULL,
            name TEXT,
            bias TEXT,
            credibility TEXT,
            country TEXT
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_domain ON sources (domain)')
    conn.commit()
    print("Database and table are set up and cleared for new import.")

def import_data(conn):
    """Đọc dữ liệu từ JSON và nạp vào SQLite."""
    print(f"Reading data from {MBFC_JSON_PATH}...")
    
    data_records = []
    try:
        with open(MBFC_JSON_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data_records.append(json.loads(line))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"FATAL ERROR: Could not read data file: {e}")
        return

    if not data_records:
        print("FATAL ERROR: JSON file is empty or could not be parsed.")
        return

    print(f"Successfully loaded {len(data_records)} records from JSON file.")

    cursor = conn.cursor()
    
    imported_count = 0
    skipped_count = 0

    for record in data_records:
        domain = record.get('domain')
        if not domain:
            skipped_count += 1
            continue

        name = record.get('page', 'Unknown')
        
        bias_value = record.get('bias_rating')
        bias = (bias_value or 'UNKNOWN').upper()

        credibility_value = record.get('factual_reporting')
        credibility = (credibility_value or 'UNKNOWN').upper()

        country = record.get('country', 'Unknown')
        
        try:
            cursor.execute('''
                INSERT INTO sources (domain, name, bias, credibility, country)
                VALUES (?, ?, ?, ?, ?)
            ''', (domain.strip(), name.strip(), bias, credibility, country))
            imported_count += 1
        except sqlite3.IntegrityError:
            skipped_count += 1

    conn.commit()
    
    print("\n--- Import Summary ---")
    print(f"Successfully imported: {imported_count} sources.")
    print(f"Skipped (no domain or duplicates): {skipped_count} sources.")
    print(f"Database is ready at {SQLITE_DB_PATH}")

def main():
    """Hàm chính điều phối toàn bộ quá trình."""
    if not download_mbfc_dataset():
        return

    # Mở kết nối MỘT LẦN DUY NHẤT
    conn = sqlite3.connect(SQLITE_DB_PATH)
    try:
        # Truyền kết nối vào các hàm
        setup_database(conn)
        import_data(conn)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Đảm bảo kết nối luôn được đóng, dù có lỗi hay không
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()