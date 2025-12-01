# scripts/import_mbfc_data.py

import sys
import json
import sqlite3
from pathlib import Path
from datasets import load_dataset


sys.path.append(str(Path(__file__).resolve().parent.parent))

from factcheck.utils.config_loader import PROJECT_ROOT
from factcheck.utils.database import DatabaseProvider

MBFC_JSON_PATH = PROJECT_ROOT / "data" / "mbfc_huggingface_data.json"


def setup_database(conn):
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
    print("Table 'sources' created.")


def main():
    print("Loading dataset from HuggingFace...")
    dataset = load_dataset("zainmujahid/mbfc-media-outlets", split="train")
    
    print("Connecting to Database via Provider...")
    conn = DatabaseProvider.get_sqlite_connection()
    
    try:
        setup_database(conn)
        cursor = conn.cursor()
        
        count = 0
        for record in dataset:
            domain = record.get('domain')
            if not domain: 
                continue
            
            try:
                cursor.execute('''
                    INSERT INTO sources (domain, name, bias, credibility, country)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    domain.strip(),
                    record.get('page', 'Unknown'),
                    (record.get('bias_rating') or 'UNKNOWN').upper(),
                    (record.get('factual_reporting') or 'UNKNOWN').upper(),
                    record.get('country', 'Unknown')
                ))
                count += 1
            except sqlite3.IntegrityError:
                pass
        
        conn.commit()
        print(f"Successfully imported {count} sources into SQLite.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()