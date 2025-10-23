# ./scripts/build_vectordb.py

import wikipediaapi
import chromadb
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm
import sys
import os
from factcheck.utils.logger import CustomLogger
# 🔥 Phải đặt trước khi import factcheck
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logger = CustomLogger(__name__).getlog()

# --- CẤU HÌNH ---
# Danh sách các chủ đề trên Wikipedia để tải về và index
WIKI_PAGES = [
    "Cancer"
]
# Tên của collection trong ChromaDB
COLLECTION_NAME = "wikipedia_knowledge"
# Đường dẫn để lưu DB trên đĩa
DB_PATH = "./chroma_db"
# Tên của mô hình embedding
EMBEDDING_MODEL_NAME = 'intfloat/e5-base-v2'


def build_database():
    """
    Tải dữ liệu từ Wikipedia, chia nhỏ, tạo vector và lưu vào ChromaDB.
    """
    logger.info("--- Starting Vector DB Build Process ---")

    # --- 1. TẢI DỮ LIỆU TỪ WIKIPEDIA ---
    logger.info(f"Downloading {len(WIKI_PAGES)} pages from Wikipedia...")
    wiki_api = wikipediaapi.Wikipedia('FailSafeFactChecker/1.0', 'en')
    documents = []
    
    for page_title in tqdm(WIKI_PAGES, desc="Fetching pages"):
        page = wiki_api.page(page_title)
        if page.exists():
            documents.append({
                "title": page_title,
                "text": page.text,
                "url": page.fullurl
            })
        else:
            logger.warning(f"Page '{page_title}' not found on Wikipedia.")

    if not documents:
        logger.error("No documents were fetched. Aborting.")
        return

    # --- 2. CHIA NHỎ VĂN BẢN (CHUNK) ---
    logger.info("Splitting documents into smaller chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len
    )
    
    all_chunks = []
    all_metadatas = []
    for doc in tqdm(documents, desc="Splitting text"):
        chunks = text_splitter.split_text(doc['text'])
        for chunk in chunks:
            all_chunks.append(chunk)
            all_metadatas.append({
                "source": doc['url'],
                "title": doc['title']
            })

    # --- 3. KHỞI TẠO CHROMA DB VÀ EMBEDDING MODEL ---
    logger.info(f"Initializing embedding model: '{EMBEDDING_MODEL_NAME}'")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    logger.info(f"Setting up ChromaDB client at path: '{DB_PATH}'")
    client = chromadb.PersistentClient(path=DB_PATH)
    
    logger.info(f"Creating or getting collection: '{COLLECTION_NAME}'")
    # Sử dụng model embedding của sentence-transformers
    from chromadb.utils import embedding_functions
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL_NAME)
    
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=sentence_transformer_ef
    )

    # --- 4. TẠO VECTOR VÀ LƯU VÀO DB ---
    logger.info(f"Generating embeddings and adding {len(all_chunks)} chunks to the database...")
    
    # ChromaDB xử lý việc tạo embedding tự động khi bạn cung cấp embedding_function
    # Chúng ta chỉ cần cung cấp văn bản.
    # Tạo ID duy nhất cho mỗi chunk
    chunk_ids = [str(i) for i in range(len(all_chunks))]
    
    # Chia thành các batch nhỏ để thêm vào DB, tránh quá tải bộ nhớ
    batch_size = 100
    for i in tqdm(range(0, len(all_chunks), batch_size), desc="Adding to DB"):
        collection.add(
            documents=all_chunks[i:i + batch_size],
            metadatas=all_metadatas[i:i + batch_size],
            ids=chunk_ids[i:i + batch_size]
        )

    logger.info("--- Creating Screening Knowledge Collection ---")
    try:
        # Cố gắng lấy collection, nếu chưa có thì tạo mới
        screening_collection = client.get_or_create_collection(
            name="screening_knowledge",
            embedding_function=sentence_transformer_ef 
        )
        logger.info(f"Successfully created or got 'screening_knowledge' collection. Current count: {screening_collection.count()}")
    except Exception as e:
        logger.error(f"Could not create/get 'screening_knowledge' collection: {e}")

    logger.info("--- Vector DB Build Process Finished! ---")
    logger.info(f"Total chunks indexed: {collection.count()}")


if __name__ == "__main__":
    build_database()