# ./factcheck/core/Decompose.pyS

from factcheck.utils.logger import CustomLogger
import nltk
import json
import networkx as nx

logger = CustomLogger(__name__).getlog()


class Decompose:
    def __init__(self, llm_client, prompt):
        """Initialize the Decompose class

        Args:
            llm_client (BaseClient): The LLM client used for decomposing documents into claims.
            prompt (BasePrompt): The prompt used for fact checking.
        """
        self.llm_client = llm_client
        self.prompt = prompt
        # self.doc2sent = self._nltk_doc2sent

    def _nltk_doc2sent(self, text: str):
        """Split the document into sentences using nltk

        Args:
            text (str): the document to be split into sentences

        Returns:
            list: a list of sentences
        """

        sentences = nltk.sent_tokenize(text)
        sentence_list = [s.strip() for s in sentences if len(s.strip()) >= 3]
        return sentence_list

    def create_sag(self, doc: str, num_retries: int = 3) -> dict:
        """
        Uses an LLM to decompose a document into a Structured Argumentation Graph (SAG).

        Args:
            doc (str): The document to be decomposed.
            num_retries (int): Maximum attempts for the LLM.

        Returns:
            dict: A dictionary representing the SAG with 'nodes' and 'edges',
                  or an empty graph if it fails.
        """
        # Sử dụng prompt mới để tạo SAG
        user_input = self.prompt.sag_prompt.format(doc=doc).strip()

        messages = self.llm_client.construct_message_list([user_input])
        for i in range(num_retries):
            response = self.llm_client.call(
                messages=messages,
                num_retries=1,
                seed=42 + i,
            )
            try:
                # Logic parse JSON an toàn
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:-3].strip()
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:-3].strip()
                
                response_dict = json.loads(cleaned_response)
                
                # Kiểm tra cấu trúc của SAG
                if "nodes" in response_dict and "edges" in response_dict:
                    logger.info(f"Successfully created SAG with {len(response_dict['nodes'])} nodes and {len(response_dict['edges'])} edges.")
                    return response_dict

            except (json.JSONDecodeError, AttributeError, TypeError) as e: 
                logger.error(f"Parse LLM response for SAG failed. Error: {e}, response: {response}")
        
        # Nếu thất bại, trả về một đồ thị rỗng để không làm sập pipeline
        logger.warning("Failed to create SAG after multiple retries. Returning an empty graph.")
        return {"nodes": [], "edges": []}

    # Giữ lại hàm restore_claims, nhưng nó có thể cần được điều chỉnh sau này
    # để hoạt động với các node của SAG thay vì list claims.
    # Hiện tại chúng ta sẽ tạm thời chưa dùng đến nó.
    
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
    def to_networkx_graph(self, sag_dict: dict):
        """Converts the SAG dictionary to a networkx DiGraph object."""
        G = nx.DiGraph()
        if "nodes" in sag_dict:
            for node in sag_dict["nodes"]:
                G.add_node(node['id'], label=node['label'], type=node['type'])
        if "edges" in sag_dict:
            for edge in sag_dict["edges"]:
                G.add_edge(edge['source'], edge['target'], label=edge['label'])
        return G