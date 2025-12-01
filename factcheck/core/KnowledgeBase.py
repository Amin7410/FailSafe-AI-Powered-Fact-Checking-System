# factcheck/core/KnowledgeBase.py

import uuid
import json
import chromadb
from factcheck.utils.logger import CustomLogger
from factcheck.utils.data_class import ClaimDetail, Evidence
from factcheck.utils.database import get_vector_collection
from factcheck.utils.config_loader import config

logger = CustomLogger(__name__).getlog()


class FactKnowledgeBase:
    def __init__(self):
        collection_name = config.get('vectordb.verified_facts_collection_name', 'verified_facts')
        
        logger.info(f"Initializing FactKnowledgeBase with collection '{collection_name}'...")
        
        try:

            from chromadb.utils import embedding_functions
            emb_model_name = config.get('vectordb.embedding_model', 'intfloat/e5-base-v2')
            
            logger.info(f"FactKnowledgeBase using embedding model: {emb_model_name}")
            
            ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=emb_model_name
            )
            
            self.collection = get_vector_collection(
                collection_name=collection_name,
                embedding_function=ef
            )

            logger.info("FactKnowledgeBase connected successfully via DatabaseProvider.") 
        except Exception as e:
            logger.error(f"Failed to connect to FactKnowledgeBase: {e}")
            self.collection = None

    def check_cache(self, claim_text: str, threshold: float = 0.2) -> ClaimDetail | None:
        if not self.collection:
            return None

        try:
            results = self.collection.query(
                query_texts=[claim_text],
                n_results=1,
                include=["metadatas", "distances", "documents"]
            )

            if not results['ids'] or not results['ids'][0]:
                return None

            distance = results['distances'][0][0]
            
            if distance < threshold:
                metadata = results['metadatas'][0][0]
                cached_claim_text = results['documents'][0][0]
                
                logger.info(f"Cache HIT! Claim '{claim_text[:30]}...' is similar to cached '{cached_claim_text[:30]}...' (Dist: {distance:.3f})")

                simulated_evidence = Evidence(
                    claim=claim_text,
                    text="[CACHED KNOWLEDGE] This claim was previously verified by FailSafe system.",
                    url="Internal Knowledge Base (Historical Data)",
                    relationship="CACHED",
                    reasoning=metadata.get('reasoning', 'No reasoning stored.')
                )

                return ClaimDetail(
                    id=-1, 
                    claim=claim_text,
                    checkworthy=True,
                    checkworthy_reason="Retrieved from Knowledge Base",
                    origin_text=claim_text,
                    start=-1, end=-1,
                    queries=[],
                    evidences=[simulated_evidence],
                    factuality=float(metadata.get('factuality', 0.5))
                )
            
            return None

        except Exception as e:
            logger.warning(f"Error checking cache: {e}")
            return None

    def save_knowledge(self, claim_detail: ClaimDetail):
        if not self.collection or not claim_detail.evidences:
            return

        try:
            fact_score = claim_detail.factuality
            if isinstance(fact_score, float):
                combined_reasoning = " || ".join([e.reasoning[:200] for e in claim_detail.evidences if e.reasoning])
                
                self.collection.add(
                    documents=[claim_detail.claim],
                    metadatas=[{
                        "factuality": fact_score,
                        "reasoning": combined_reasoning[:1000] 
                    }],
                    ids=[str(uuid.uuid4())]
                )
                logger.info(f"Saved new knowledge: '{claim_detail.claim[:30]}...'")

        except Exception as e:
            logger.error(f"Failed to save knowledge: {e}")