"""
Multilingual Service

Handles language detection, translation, and cross-lingual analysis.
"""

import logging
from typing import Dict, Any, Optional, List
import re
import numpy as np

logger = logging.getLogger(__name__)


class MultilingualService:
    """Service for multilingual content processing"""
    
    def __init__(self):
        self.supported_languages = ["en", "es", "fr", "de", "zh", "ar", "ja", "ko"]
        self.language_patterns = {
            "en": r'\b(the|and|or|but|in|on|at|to|for|of|with|by)\b',
            "es": r'\b(el|la|los|las|y|o|pero|en|con|por|para|de)\b',
            "fr": r'\b(le|la|les|et|ou|mais|dans|avec|pour|de|du|des)\b',
            "de": r'\b(der|die|das|und|oder|aber|in|mit|für|von|zu)\b',
            "zh": r'[\u4e00-\u9fff]',
            "ar": r'[\u0600-\u06ff]',
            "ja": r'[\u3040-\u309f\u30a0-\u30ff]',
            "ko": r'[\uac00-\ud7af]'
        }
    
    def process_multilingual_content(self, content: str, preferred_language: Optional[str] = None) -> Dict[str, Any]:
        """
        Process multilingual content
        
        Args:
            content: Content to process
            preferred_language: Preferred language code
            
        Returns:
            Dict containing multilingual processing results
        """
        try:
            # Detect language
            detected_language = self._detect_language(content)
            processing_language = preferred_language or detected_language
            
            # Translation info (pivot to English if needed)
            translation_info = None
            pivot_lang = processing_language or detected_language
            if detected_language != pivot_lang:
                translation_info = self._get_translation_info(content, detected_language, pivot_lang)
            
            # Cross-lingual mappings: map concepts to English keys for KG
            cross_lingual_mappings = self._generate_cross_lingual_mappings(
                translation_info["translated_text"] if translation_info else content,
                pivot_lang
            )
            
            # SAG data for multilingual
            sag_data = self._generate_multilingual_sag_data(content, processing_language)
            
            result = {
                "language_detection": {
                    "language": detected_language,
                    "confidence": 0.8,
                    "method": "pattern_matching"
                },
                "translation": translation_info,
                "cross_lingual_analysis": {
                    "mappings": cross_lingual_mappings,
                    "supported_languages": self.supported_languages
                },
                "sag_data": sag_data
            }
            
            logger.info(f"Multilingual processing completed: {detected_language} -> {processing_language}")
            return result
            
        except Exception as e:
            logger.error(f"Error in multilingual processing: {e}")
            return {
                "language_detection": {"language": "en", "confidence": 0.0, "method": "error"},
                "translation": None,
                "cross_lingual_analysis": {"mappings": [], "supported_languages": self.supported_languages},
                "sag_data": {}
            }
    
    def _detect_language(self, content: str) -> str:
        """Detect content language"""
        try:
            content_lower = content.lower()
            scores = {}
            
            for lang, pattern in self.language_patterns.items():
                matches = len(re.findall(pattern, content_lower))
                scores[lang] = matches
            
            if not scores or max(scores.values()) == 0:
                return "en"  # Default to English
            
            detected = max(scores, key=scores.get)
            return detected
            
        except Exception as e:
            logger.warning(f"Language detection error: {e}")
            return "en"
    
    def _get_translation_info(self, content: str, source_lang: str, target_lang: str) -> Optional[Dict[str, Any]]:
        """Get translation information"""
        if source_lang == target_lang:
            return None
        
        return {
            "translated_text": content,  # Simplified - in real implementation, would translate
            "source_language": source_lang,
            "target_language": target_lang,
            "confidence": 0.7,
            "method": "simulated_translation"
        }
    
    def _generate_cross_lingual_mappings(self, content: str, language: str) -> list:
        """Generate cross-lingual concept mappings"""
        mappings = []
        
        # Extract key concepts (simplified)
        concepts = self._extract_concepts(content)
        
        for concept in concepts[:5]:  # Limit to 5 concepts
            mapping = {
                "source_concept": concept,
                "target_concept": concept,  # Simplified
                "source_language": language,
                "target_language": "en",
                "concept_key": concept.lower().replace(" ", "_"),
                "confidence": 0.8,
                "method": "concept_extraction"
            }
            mappings.append(mapping)
        
        return mappings
    
    def _extract_concepts(self, content: str) -> list:
        """Extract key concepts from content"""
        # Simple concept extraction based on capitalized words and important terms
        words = content.split()
        concepts = []
        
        for word in words:
            if len(word) > 3 and word[0].isupper():
                concepts.append(word.strip('.,!?'))
        
        return concepts[:10]  # Limit to 10 concepts
    
    def _generate_multilingual_sag_data(self, content: str, language: str) -> Dict[str, Any]:
        """Generate multilingual SAG data"""
        return {
            "language": language,
            "concepts": self._extract_concepts(content),
            "entities": [],  # Would be populated by NER
            "relations": [],  # Would be populated by relation extraction
            "metadata": {
                "processing_language": language,
                "concept_count": len(self._extract_concepts(content))
            }
        }
    
class MultilingualEmbeddingService:
    """
    Service for generating multilingual text embeddings.
    This class was reconstructed based on usage in other files.
    """
    def __init__(self):
        self.model = self._load_model()
        self.supported_languages = ["en", "vi", "es", "fr", "de", "zh", "ja", "ko", "ar", "hi"]

    def _load_model(self):
        """Loads the multilingual sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            # Using a popular multilingual model
            return SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        except ImportError:
            logger.warning("sentence-transformers is not installed. Multilingual embeddings will not work.")
            return None
        except Exception as e:
            logger.error(f"Failed to load multilingual embedding model: {e}")
            return None

    def is_language_supported(self, language_code: str) -> bool:
        """Checks if a language is supported by the embedding model."""
        return language_code in self.supported_languages

    def get_supported_languages(self) -> List[str]:
        """Returns the list of supported languages."""
        return self.supported_languages

    def embed_texts(self, texts: List[str], lang: str) -> np.ndarray:
        """Generates embeddings for a list of texts in a specific language."""
        import numpy as np
        
        if self.model is None or not self.is_language_supported(lang):
            logger.warning(f"Using fallback (random) embeddings for language '{lang}'.")
            # Return random embeddings of the correct shape if model fails
            return np.random.rand(len(texts), 384).astype(np.float32)

        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return np.asarray(embeddings, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error generating multilingual embeddings: {e}")
            return np.random.rand(len(texts), 384).astype(np.float32)