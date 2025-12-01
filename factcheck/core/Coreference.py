# factcheck/core/Coreference.py
from fastcoref import FCoref
from factcheck.utils.logger import CustomLogger
import torch

logger = CustomLogger(__name__).getlog()


class ReferenceResolver:
    def __init__(self, model_name: str = 'f-coref-base', device: str = None):
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device    
        logger.info(f"Initializing ReferenceResolver with model '{model_name}' on device '{self.device}'...")
        try:
            self.model = FCoref(device=self.device)
            logger.info("ReferenceResolver initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize ReferenceResolver: {e}")
            self.model = None

    def resolve(self, text: str) -> str:
        if not self.model or not text:
            return text

        try:
            preds = self.model.predict(texts=[text])
            clusters = preds[0].get_clusters(as_strings=False)
            replacements = []
            for cluster in clusters:
                main_mention_span = cluster[0] 
                main_mention_text = text[main_mention_span[0]:main_mention_span[1]]
                
                for i in range(1, len(cluster)):
                    span = cluster[i]
                    mention_text = text[span[0]:span[1]]
                    if len(mention_text) < len(main_mention_text) or mention_text.lower() in ['he', 'she', 'it', 'they', 'him', 'her', 'them', 'his', 'its', 'their']:
                        replacements.append((span[0], span[1], main_mention_text))
            replacements.sort(key=lambda x: x[0], reverse=True)
            resolved_text = list(text)
            for start, end, replacement in replacements:
                resolved_text[start:end] = list(replacement)  
            return "".join(resolved_text)
        except Exception as e:
            logger.warning(f"Error during coreference resolution: {e}. Returning original text.")
            return text


if __name__ == '__main__':
    resolver = ReferenceResolver(device='cpu')
    text = "Elon Musk is a billionaire. He owns Tesla and SpaceX. They are huge companies."
    print(f"Original: {text}")
    print(f"Resolved: {resolver.resolve(text)}")