# factcheck/utils/database.py

import sqlite3
import chromadb
from chromadb.config import Settings
from factcheck.utils.config_loader import config, PROJECT_ROOT
from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()


class DatabaseProvider:
    _sqlite_conn = None
    _chroma_client = None

    @classmethod
    def get_sqlite_connection(cls):
        rel_path = config.get('database.sqlite_path', 'data/sources.db')
        db_path = str(PROJECT_ROOT / rel_path)

        try:
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row 
            return conn
        except sqlite3.Error as e:
            logger.error(f"FATAL: Cannot connect to SQLite at {db_path}: {e}")
            raise e

    @classmethod
    def get_chroma_client(cls):
        if cls._chroma_client:
            return cls._chroma_client

        mode = config.get('database.chroma_mode', 'local')

        try:
            if mode == 'server':
                host = config.get('database.chroma_host', 'localhost')
                port = config.get('database.chroma_port', 8000)
                logger.info(f"Connecting to ChromaDB Server at {host}:{port}...")
                cls._chroma_client = chromadb.HttpClient(host=host, port=port)
            else:
                rel_path = config.get('database.chroma_path', 'chroma_db')
                db_path = str(PROJECT_ROOT / rel_path)
                logger.info(f"Connecting to ChromaDB Local at {db_path}...")
                cls._chroma_client = chromadb.PersistentClient(path=db_path)
            
            return cls._chroma_client
        except Exception as e:
            logger.error(f"FATAL: Cannot connect to ChromaDB: {e}")
            raise e


def get_db_cursor():
    conn = DatabaseProvider.get_sqlite_connection()
    return conn.cursor()


def get_vector_collection(collection_name, embedding_function=None):
    client = DatabaseProvider.get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name, 
        embedding_function=embedding_function
    )