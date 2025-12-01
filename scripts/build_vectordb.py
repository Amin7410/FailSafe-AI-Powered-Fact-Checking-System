# scripts/build_vectordb.py

import sys
import wikipediaapi
from tqdm import tqdm
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter


sys.path.append(str(Path(__file__).resolve().parent.parent))

from factcheck.utils.config_loader import config
from factcheck.utils.database import get_vector_collection
from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()

COLLECTION_NAME = config.get('vectordb.collection_name')
WIKI_PAGES = ["Artificial intelligence"]


def build_database():
    logger.info("--- Starting Vector DB Build ---")

    wiki = wikipediaapi.Wikipedia('FailSafeBot/1.0', 'en')
    docs = []
    for title in tqdm(WIKI_PAGES, desc="Fetching Wiki"):
        page = wiki.page(title)
        if page.exists():
            docs.append({"text": page.text, "meta": {"source": page.fullurl, "title": title}})

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = []
    metadatas = []
    ids = []
    
    global_idx = 0
    for doc in docs:
        splits = splitter.split_text(doc['text'])
        for s in splits:
            chunks.append(s)
            metadatas.append(doc['meta'])
            ids.append(f"{doc['meta']['title']}_{global_idx}")
            global_idx += 1

    logger.info(f"Ingesting {len(chunks)} chunks into collection '{COLLECTION_NAME}'...")
    
    try:
        from chromadb.utils import embedding_functions
        EMBEDDING_MODEL_NAME = config.get('vectordb.embedding_model')
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )
        
        collection = get_vector_collection(
            collection_name=COLLECTION_NAME,
            embedding_function=sentence_transformer_ef
        )
        batch_size = 100
        for i in tqdm(range(0, len(chunks), batch_size), desc="Indexing"):
            collection.add(
                documents=chunks[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size],
                ids=ids[i:i + batch_size]
            )
        logger.info("Build VectorDB Finished!")
        
    except Exception:
        logger.error("Failed to build VectorDB: {e}")


if __name__ == "__main__":
    build_database()