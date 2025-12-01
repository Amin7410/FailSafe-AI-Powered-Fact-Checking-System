# ./factcheck/core/Decompose.pyS

from factcheck.utils.logger import CustomLogger
import nltk
import json
import networkx as nx
from factcheck.utils.graph_utils import sag_to_graph, graph_to_networkx_dict
from sentence_transformers import SentenceTransformer, util

logger = CustomLogger(__name__).getlog()


class Decompose:
    def __init__(self, llm_client, prompt):
        self.llm_client = llm_client
        self.prompt = prompt

        logger.info("Loading deduplication model (all-MiniLM-L6-v2)...")
        try:
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers: {e}. Deduplication will be skipped.")
            self.embedder = None

    def create_sag(self, doc: str, num_retries: int = 3) -> dict:
        user_input = self.prompt.sag_prompt.format(doc=doc).strip()
        messages = self.llm_client.construct_message_list([user_input])

        for i in range(num_retries):
            response = self.llm_client.call(
                messages=messages,
                num_retries=1,
                seed=42 + i,
            )
            try:
                print(f"\n[DEBUG] Raw LLM Response (Attempt {i + 1}):\n{response}\n[END DEBUG]\n")

                response_dict = {}
                if isinstance(response, dict):
                    response_dict = response
                elif isinstance(response, str):
                    cleaned_response = response.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = cleaned_response[7:-3].strip()
                    elif cleaned_response.startswith("```"):
                        cleaned_response = cleaned_response[3:-3].strip()
                    response_dict = json.loads(cleaned_response)
                else:
                    logger.error(f"LLM returned unexpected type: {type(response)}")
                    continue
                if "@graph" in response_dict:
                    logger.info(f"Successfully created SAG with {len(response_dict.get('@graph', []))} nodes.")
                    if "@context" not in response_dict:
                        response_dict["@context"] = "https://failsafe.factcheck.ai/ontology#"
                    return response_dict
                else:
                    logger.warning(f"Response is valid but missing '@graph' key.")

            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Failed to process LLM response for SAG. Error: {e}")     
        logger.warning("Failed to create SAG after multiple retries. Returning an empty graph.")
        return {"@context": "https://failsafe.factcheck.ai/ontology#", "@graph": []}
    
    def deduplicate_claims(self, claims: list[str], threshold: float = 0.85) -> list[str]:
        if not claims or len(claims) < 2 or self.embedder is None:
            return claims

        logger.info(f"Deduplicating {len(claims)} claims with threshold {threshold}...")
        embeddings = self.embedder.encode(claims, convert_to_tensor=True)
        cosine_scores = util.cos_sim(embeddings, embeddings)
        sorted_indices = sorted(range(len(claims)), key=lambda k: len(claims[k]), reverse=True)
        
        kept_indices = []
        
        for idx in sorted_indices:
            is_duplicate = False
            for kept_idx in kept_indices:
                score = cosine_scores[idx][kept_idx]
                if score >= threshold:
                    logger.info(f"Duplicate found: '{claims[idx][:30]}...' is similar to '{claims[kept_idx][:30]}...' (Score: {score:.4f})")
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                kept_indices.append(idx)
        kept_indices.sort()
        final_claims = [claims[i] for i in kept_indices]
        
        logger.info(f"Deduplication complete. Reduced from {len(claims)} to {len(final_claims)} claims.")
        return final_claims

    def restore_claims(self, doc: str, claims: list, num_retries: int = 3, prompt: str = None) -> dict[str, dict]:
        if prompt is None:
            user_input = self.prompt.restore_prompt.format(doc=doc, claims=claims).strip()
        else:
            user_input = prompt.format(doc=doc, claims=claims).strip()

        messages = self.llm_client.construct_message_list([user_input])
        
        for i in range(num_retries):
            response = self.llm_client.call(
                messages=messages,
                num_retries=1,
                seed=42 + i,
            )
            try:
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:-3].strip()
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:-3].strip()
                claim2text = json.loads(cleaned_response)

                if isinstance(claim2text, dict) and len(claim2text) == len(claims):

                    claim2doc_detail = {}
                    for claim, text_span in claim2text.items():
                        start_index = doc.find(text_span)
                        if start_index == -1:
                            start_index = -1 
                            end_index = -1
                        else:
                            end_index = start_index + len(text_span)
                            
                        claim2doc_detail[claim] = {
                            "text": text_span,
                            "start": start_index,
                            "end": end_index
                        }
                    
                    logger.info("Successfully restored claims to document spans.")
                    return claim2doc_detail 

            except Exception as e:
                logger.error(f"Parse LLM response error in restore_claims: {e}, response is: {response}")
                logger.error(f"Prompt was: {messages}")

        logger.warning("Failed to restore claims after multiple retries. Returning empty mapping.")
        empty_mapping = {claim: {"text": "", "start": -1, "end": -1} for claim in claims}
        return empty_mapping

    def to_networkx_graph_dict(self, sag_jsonld: dict) -> dict:
        if not sag_jsonld:
            return {"nodes": [], "edges": []}
            
        graph = sag_to_graph(sag_jsonld)
        return graph_to_networkx_dict(graph)