# ./factcheck/core/Retriever/hybrid_retriever.py

import chromadb
from sentence_transformers import SentenceTransformer
from .serper_retriever import SerperEvidenceRetriever
from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()

# --- CẤU HÌNH ---
COLLECTION_NAME = "wikipedia_knowledge"
DB_PATH = "./chroma_db"
EMBEDDING_MODEL_NAME = 'intfloat/e5-base-v2'

VECTOR_SEARCH_DISTANCE_THRESHOLD = 0.2


class HybridRetriever:
    def __init__(self, llm_client, api_config: dict = None):
        """
        Initializes the HybridRetriever.
        """
        logger.info("Initializing HybridRetriever...")
        self.llm_client = llm_client

        try:
            logger.info(f"Loading embedding model '{EMBEDDING_MODEL_NAME}'...")
            # Không cần tải model ở đây, ChromaDB sẽ tự làm
            
            client = chromadb.PersistentClient(path=DB_PATH)
            
            from chromadb.utils import embedding_functions
            embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL_NAME
            )
            
            self.collection = client.get_collection(
                name=COLLECTION_NAME,
                embedding_function=embedding_function
            )
            logger.info(f"Successfully connected to ChromaDB collection '{COLLECTION_NAME}'.")

        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}. Vector search will be disabled.")
            self.collection = None

        self.web_retriever = SerperEvidenceRetriever(llm_client, api_config)

    def _search_vector_db(self, query: str, top_k: int = 3) -> list:
        """Searches the local vector database and filters results by a distance threshold."""
        if not self.collection:
            return []

        try:
            # Truy vấn và yêu cầu trả về cả "distances"
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["metadatas", "documents", "distances"] 
            )
            
            evidences = []
            if results and results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    distance = results['distances'][0][i]
                    
                    # --- BỘ LỌC NGƯỠNG TIN CẬY ---
                    if distance <= VECTOR_SEARCH_DISTANCE_THRESHOLD:
                        evidences.append({
                            "text": results['documents'][0][i],
                            "url": results['metadatas'][0][i]['source'],
                            "trust_level": "high"
                        })
                        logger.info(f"Accepting Vector DB result with distance {distance:.4f} (<= threshold {VECTOR_SEARCH_DISTANCE_THRESHOLD}).")
                    else:
                        logger.warning(f"Discarding Vector DB result with distance {distance:.4f} (> threshold {VECTOR_SEARCH_DISTANCE_THRESHOLD}). Too irrelevant.")

                logger.info(f"Found {len(evidences)} relevant results for query '{query[:30]}...' in Vector DB.")
            else:
                logger.info(f"Found 0 results for query '{query[:30]}...' in Vector DB.")

            return evidences
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            return []

    def retrieve_evidence(self, claim_queries_dict, top_k: int = 3, **kwargs):
        """
        Retrieves evidence using a hybrid approach.
        """
        final_claim_evidence_dict = {}

        for claim, queries in claim_queries_dict.items():
            all_evidences_for_claim = []
            
            if not queries:
                final_claim_evidence_dict[claim] = []
                continue

            primary_query = queries[0]
            
            # --- BƯỚC 1: TÌM TRONG VECTOR DB TRƯỚC ---
            vector_db_evidences = self._search_vector_db(primary_query, top_k=top_k)
            all_evidences_for_claim.extend(vector_db_evidences)
            
            # --- BƯỚC 2: NẾU CẦN, TÌM THÊM TRÊN WEB ---
            if len(all_evidences_for_claim) < top_k:
                logger.info(f"Not enough results from Vector DB for claim '{claim[:50]}...'. Falling back to web search.")
                
                temp_claim_queries = {claim: queries}
                web_evidences_dict = self.web_retriever.retrieve_evidence(
                    claim_queries_dict=temp_claim_queries,
                    top_k=top_k
                )
                
                web_evidences = web_evidences_dict.get(claim, [])
                all_evidences_for_claim.extend(web_evidences)

            # Loại bỏ các bằng chứng trùng lặp (dựa trên URL)
            unique_evidences = {ev['url']: ev for ev in all_evidences_for_claim}.values()
            final_claim_evidence_dict[claim] = list(unique_evidences)
            
        return final_claim_evidence_dict