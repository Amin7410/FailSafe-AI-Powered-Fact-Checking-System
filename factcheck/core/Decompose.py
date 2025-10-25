# ./factcheck/core/Decompose.pyS

from factcheck.utils.logger import CustomLogger
import nltk
import json
import networkx as nx
from factcheck.utils.graph_utils import sag_to_graph, graph_to_networkx_dict

logger = CustomLogger(__name__).getlog()


class Decompose:
    def __init__(self, llm_client, prompt):
        self.llm_client = llm_client
        self.prompt = prompt

    def create_sag(self, doc: str, num_retries: int = 3) -> dict:
        user_input = self.prompt.sag_prompt.format(doc=doc).strip()
        messages = self.llm_client.construct_message_list([user_input])

        for i in range(num_retries):
            # response có thể là str (từ GPT) hoặc dict (từ Gemini)
            response = self.llm_client.call(
                messages=messages,
                num_retries=1,
                seed=42 + i,
            )
            try:
                print(f"\n[DEBUG] Raw LLM Response (Attempt {i + 1}):\n{response}\n[END DEBUG]\n")

                response_dict = {}
                # === SỬA LỖI LOGIC: XỬ LÝ CẢ STR VÀ DICT ===
                if isinstance(response, dict):
                    # Nếu đã là dict (từ Gemini), dùng trực tiếp
                    response_dict = response
                elif isinstance(response, str):
                    # Nếu là chuỗi (từ GPT), thì parse nó
                    cleaned_response = response.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = cleaned_response[7:-3].strip()
                    elif cleaned_response.startswith("```"):
                        cleaned_response = cleaned_response[3:-3].strip()
                    response_dict = json.loads(cleaned_response)
                else:
                    # Trường hợp không mong muốn
                    logger.error(f"LLM returned unexpected type: {type(response)}")
                    continue  # Bỏ qua lần thử này
                # === KẾT THÚC SỬA LỖI ===
                
                if "@graph" in response_dict:
                    logger.info(f"Successfully created SAG with {len(response_dict.get('@graph', []))} nodes.")
                    # Đảm bảo có @context trước khi trả về
                    if "@context" not in response_dict:
                        response_dict["@context"] = "https://failsafe.factcheck.ai/ontology#"
                    return response_dict
                else:
                    logger.warning(f"Response is valid but missing '@graph' key.")

            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Failed to process LLM response for SAG. Error: {e}")     
        logger.warning("Failed to create SAG after multiple retries. Returning an empty graph.")
        return {"@context": "https://failsafe.factcheck.ai/ontology#", "@graph": []}
    
    def restore_claims(self, doc: str, claims: list, num_retries: int = 3, prompt: str = None) -> dict[str, dict]:
        """
        Use Gemini to map claims back to the document.
        This version is more lenient and focuses on getting a mapping,
        even if it's not a perfect concatenation of the original doc.
        """

        # --- LOGIC CŨ ĐÃ BỊ XÓA ---
        # def restore(claim2doc): ...
        
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
                
                # Sửa từ eval thành json.loads cho an toàn
                claim2text = json.loads(cleaned_response)
                
                # Kiểm tra cơ bản: có phải dict và có đúng số lượng claims không
                if isinstance(claim2text, dict) and len(claim2text) == len(claims):
                    
                    # Chuyển đổi sang định dạng đầu ra mong muốn
                    claim2doc_detail = {}
                    for claim, text_span in claim2text.items():
                        # Cố gắng tìm vị trí của span trong văn bản gốc
                        start_index = doc.find(text_span)
                        if start_index == -1:
                            # Nếu không tìm thấy, gán vị trí không xác định
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

        # Nếu sau tất cả các lần thử vẫn thất bại, trả về một cấu trúc rỗng
        # để hệ thống không bị sập
        logger.warning("Failed to restore claims after multiple retries. Returning empty mapping.")
        # Tạo mapping rỗng với cấu trúc đúng để tránh lỗi ở các bước sau
        empty_mapping = {claim: {"text": "", "start": -1, "end": -1} for claim in claims}
        return empty_mapping

    # Hàm tiện ích để chuyển đổi dict SAG thành đối tượng networkx
    def to_networkx_graph_dict(self, sag_jsonld: dict) -> dict:
        """
        Converts the SAG JSON-LD object to a dictionary format suitable for NetworkX.
        This now uses the centralized graph utility function.
        """
        if not sag_jsonld:
            return {"nodes": [], "edges": []}
            
        graph = sag_to_graph(sag_jsonld)
        return graph_to_networkx_dict(graph)