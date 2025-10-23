# factcheck/core/Coreference.py
from fastcoref import FCoref
from factcheck.utils.logger import CustomLogger
import torch

logger = CustomLogger(__name__).getlog()


class ReferenceResolver:
    def __init__(self, model_name: str = 'f-coref-base', device: str = None):
        """
        Initializes the ReferenceResolver with a fastcoref model.
        Args:
            model_name (str): 'f-coref-base' (faster) or 'linguistic-knowledge-coref' (more accurate but larger).
            device (str): 'cpu' or 'cuda'. If None, automatically detects.
        """
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
            
        logger.info(f"Initializing ReferenceResolver with model '{model_name}' on device '{self.device}'...")
        try:
            # FCoref là mô hình nhanh và nhẹ hơn, phù hợp cho hầu hết các trường hợp
            self.model = FCoref(device=self.device)
            logger.info("ReferenceResolver initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize ReferenceResolver: {e}")
            self.model = None

    def resolve(self, text: str) -> str:
        """
        Resolves coreferences in the given text.
        Replaces pronouns with the entities they refer to.
        """
        if not self.model or not text:
            return text

        try:
            # fastcoref có hàm get_clusters để lấy các cụm tham chiếu
            # nhưng chúng ta muốn thay thế trực tiếp vào văn bản.
            # Rất may, các mô hình mới thường có phương thức hỗ trợ hoặc ta có thể tự làm.
            # FCoref không có hàm .resolve() trực tiếp trả về text đã thay thế như một số thư viện cũ.
            # Chúng ta sẽ dùng get_clusters và tự thay thế.
            
            preds = self.model.predict(texts=[text])
            
            # Lấy các cụm (clusters) tham chiếu. 
            # Mỗi cụm là một danh sách các span (vị trí bắt đầu, kết thúc) cùng chỉ một thực thể.
            clusters = preds[0].get_clusters(as_strings=False)
            
            # Để thay thế, chúng ta cần xử lý từ cuối văn bản lên đầu 
            # để không làm thay đổi các chỉ số (indices) của các phần chưa xử lý.
            
            # 1. Tạo danh sách tất cả các thay thế cần thực hiện
            replacements = []
            for cluster in clusters:
                # Tìm thực thể đại diện (thường là cụm dài nhất hoặc xuất hiện đầu tiên)
                # Ở đây ta chọn span đầu tiên trong cụm làm đại diện (thường là tên riêng xuất hiện lần đầu)
                main_mention_span = cluster[0] 
                main_mention_text = text[main_mention_span[0]:main_mention_span[1]]
                
                for i in range(1, len(cluster)):
                    span = cluster[i]
                    # Chỉ thay thế nếu là đại từ hoặc cụm từ ngắn hơn đáng kể
                    mention_text = text[span[0]:span[1]]
                    # Một logic đơn giản: nếu mention hiện tại ngắn hơn main mention, hãy thay thế nó
                    # (Tránh thay "Elon Musk" bằng "Elon" nếu cả hai cùng cụm)
                    if len(mention_text) < len(main_mention_text) or mention_text.lower() in ['he', 'she', 'it', 'they', 'him', 'her', 'them', 'his', 'its', 'their']:
                        replacements.append((span[0], span[1], main_mention_text))
            
            # 2. Sắp xếp các thay thế theo thứ tự ngược từ cuối văn bản lên đầu
            replacements.sort(key=lambda x: x[0], reverse=True)
            
            # 3. Thực hiện thay thế
            resolved_text = list(text)
            for start, end, replacement in replacements:
                resolved_text[start:end] = list(replacement)
            
            return "".join(resolved_text)

        except Exception as e:
            logger.warning(f"Error during coreference resolution: {e}. Returning original text.")
            return text


if __name__ == '__main__':
    # Test nhanh
    resolver = ReferenceResolver(device='cpu')
    text = "Elon Musk is a billionaire. He owns Tesla and SpaceX. They are huge companies."
    print(f"Original: {text}")
    print(f"Resolved: {resolver.resolve(text)}")