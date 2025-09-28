"""
Synthetic Data Generator for FailSafe Testing
Generates realistic test data for adversarial testing and quality assurance
"""

import random
import string
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DataType(Enum):
    """Types of synthetic data to generate"""
    TRUE_CLAIMS = "true_claims"
    FALSE_CLAIMS = "false_claims"
    MIXED_CLAIMS = "mixed_claims"
    UNVERIFIABLE_CLAIMS = "unverifiable_claims"
    EVIDENCE = "evidence"
    FALLACIES = "fallacies"
    MULTILINGUAL = "multilingual"

@dataclass
class SyntheticClaim:
    """Synthetic claim data structure"""
    text: str
    verdict: str
    confidence: float
    category: str
    language: str
    metadata: Dict[str, Any]

@dataclass
class SyntheticEvidence:
    """Synthetic evidence data structure"""
    source: str
    title: str
    snippet: str
    score: float
    source_type: str
    reliability: float
    metadata: Dict[str, Any]

class SyntheticDataGenerator:
    """Generate synthetic data for testing purposes"""
    
    def __init__(self):
        self.true_claim_templates = self._load_true_claim_templates()
        self.false_claim_templates = self._load_false_claim_templates()
        self.mixed_claim_templates = self._load_mixed_claim_templates()
        self.unverifiable_claim_templates = self._load_unverifiable_claim_templates()
        self.evidence_templates = self._load_evidence_templates()
        self.fallacy_templates = self._load_fallacy_templates()
        self.multilingual_templates = self._load_multilingual_templates()
    
    def _load_true_claim_templates(self) -> List[Dict[str, Any]]:
        """Load templates for true claims"""
        return [
            {
                "template": "The Earth is {shape} and {orbits} around the Sun.",
                "variables": {
                    "shape": ["round", "spherical", "a sphere"],
                    "orbits": ["orbits", "revolves", "circles"]
                },
                "category": "science",
                "confidence": 0.95
            },
            {
                "template": "Water boils at {temperature} at sea level.",
                "variables": {
                    "temperature": ["100°C", "212°F", "100 degrees Celsius"]
                },
                "category": "science",
                "confidence": 0.98
            },
            {
                "template": "The human heart has {chambers} chambers.",
                "variables": {
                    "chambers": ["four", "4", "4 main"]
                },
                "category": "biology",
                "confidence": 0.99
            },
            {
                "template": "The capital of {country} is {capital}.",
                "variables": {
                    "country": ["France", "Germany", "Japan", "Australia"],
                    "capital": ["Paris", "Berlin", "Tokyo", "Canberra"]
                },
                "category": "geography",
                "confidence": 0.97
            },
            {
                "template": "The speed of light is approximately {speed} in a vacuum.",
                "variables": {
                    "speed": ["299,792,458 m/s", "3 × 10⁸ m/s", "186,282 miles per second"]
                },
                "category": "physics",
                "confidence": 0.99
            }
        ]
    
    def _load_false_claim_templates(self) -> List[Dict[str, Any]]:
        """Load templates for false claims"""
        return [
            {
                "template": "The Earth is {shape} and {position}.",
                "variables": {
                    "shape": ["flat", "square", "triangular"],
                    "position": ["the center of the universe", "stationary", "the only planet"]
                },
                "category": "science",
                "confidence": 0.95
            },
            {
                "template": "Water boils at {temperature} at sea level.",
                "variables": {
                    "temperature": ["50°C", "150°C", "200°F"]
                },
                "category": "science",
                "confidence": 0.98
            },
            {
                "template": "The human heart has {chambers} chambers.",
                "variables": {
                    "chambers": ["two", "2", "three", "3"]
                },
                "category": "biology",
                "confidence": 0.99
            },
            {
                "template": "The capital of {country} is {capital}.",
                "variables": {
                    "country": ["France", "Germany", "Japan", "Australia"],
                    "capital": ["London", "Madrid", "Beijing", "New York"]
                },
                "category": "geography",
                "confidence": 0.97
            },
            {
                "template": "The speed of light is approximately {speed} in a vacuum.",
                "variables": {
                    "speed": ["100 m/s", "1,000 km/h", "50 miles per hour"]
                },
                "category": "physics",
                "confidence": 0.99
            }
        ]
    
    def _load_mixed_claim_templates(self) -> List[Dict[str, Any]]:
        """Load templates for mixed claims (partially true/false)"""
        return [
            {
                "template": "Climate change is {cause} and {impact}.",
                "variables": {
                    "cause": ["caused by human activities", "a natural phenomenon", "due to solar cycles"],
                    "impact": ["will cause sea levels to rise", "has no significant effects", "will lead to global cooling"]
                },
                "category": "environment",
                "confidence": 0.75
            },
            {
                "template": "Social media {effect} and {impact}.",
                "variables": {
                    "effect": ["improves communication", "reduces face-to-face interaction", "increases misinformation"],
                    "impact": ["enhances democracy", "threatens privacy", "promotes social connection"]
                },
                "category": "technology",
                "confidence": 0.70
            },
            {
                "template": "Artificial intelligence will {prediction} and {consequence}.",
                "variables": {
                    "prediction": ["create new jobs", "replace human workers", "solve complex problems"],
                    "consequence": ["improve quality of life", "increase unemployment", "enhance productivity"]
                },
                "category": "technology",
                "confidence": 0.65
            }
        ]
    
    def _load_unverifiable_claim_templates(self) -> List[Dict[str, Any]]:
        """Load templates for unverifiable claims"""
        return [
            {
                "template": "The {entity} is {attribute} because {reason}.",
                "variables": {
                    "entity": ["universe", "human consciousness", "quantum mechanics"],
                    "attribute": ["infinite", "mysterious", "incomprehensible"],
                    "reason": ["we cannot fully understand it", "it transcends our perception", "it exists beyond our reality"]
                },
                "category": "philosophy",
                "confidence": 0.30
            },
            {
                "template": "In the future, {prediction} will {outcome}.",
                "variables": {
                    "prediction": ["technology", "humanity", "society"],
                    "outcome": ["evolve beyond recognition", "achieve perfection", "face ultimate destruction"]
                },
                "category": "futurism",
                "confidence": 0.25
            },
            {
                "template": "The meaning of {concept} is {interpretation}.",
                "variables": {
                    "concept": ["life", "existence", "reality"],
                    "interpretation": ["subjective and personal", "universal and absolute", "unknowable and mysterious"]
                },
                "category": "philosophy",
                "confidence": 0.20
            }
        ]
    
    def _load_evidence_templates(self) -> List[Dict[str, Any]]:
        """Load templates for synthetic evidence"""
        return [
            {
                "source": "https://example.com/study-{id}",
                "title": "Study on {topic} shows {finding}",
                "snippet": "According to the research, {topic} demonstrates {finding} with {confidence} confidence.",
                "source_type": "academic",
                "reliability": 0.85,
                "variables": {
                    "id": ["001", "002", "003", "004", "005"],
                    "topic": ["climate change", "vaccine efficacy", "economic growth", "social media impact"],
                    "finding": ["significant effects", "positive outcomes", "negative consequences", "mixed results"],
                    "confidence": ["high", "moderate", "statistical", "strong"]
                }
            },
            {
                "source": "https://news.example.com/article-{id}",
                "title": "Breaking: {topic} {outcome}",
                "snippet": "Recent reports indicate that {topic} has {outcome} in {location}.",
                "source_type": "news",
                "reliability": 0.70,
                "variables": {
                    "id": ["001", "002", "003", "004", "005"],
                    "topic": ["economic policy", "health measures", "environmental regulations", "social programs"],
                    "outcome": ["shown positive results", "faced criticism", "gained support", "encountered challenges"],
                    "location": ["the United States", "Europe", "Asia", "globally"]
                }
            },
            {
                "source": "https://expert.example.com/opinion-{id}",
                "title": "Expert opinion on {topic}",
                "snippet": "Dr. {expert} from {institution} states that {topic} is {assessment}.",
                "source_type": "expert",
                "reliability": 0.80,
                "variables": {
                    "id": ["001", "002", "003", "004", "005"],
                    "topic": ["medical treatment", "scientific research", "policy implementation", "technological advancement"],
                    "expert": ["Smith", "Johnson", "Williams", "Brown", "Davis"],
                    "institution": ["Harvard University", "MIT", "Stanford", "Oxford", "Cambridge"],
                    "assessment": ["promising", "concerning", "revolutionary", "questionable", "significant"]
                }
            }
        ]
    
    def _load_fallacy_templates(self) -> List[Dict[str, Any]]:
        """Load templates for logical fallacies"""
        return [
            {
                "template": "You can't trust {person} because {personal_attack}.",
                "fallacy_type": "ad_hominem",
                "variables": {
                    "person": ["him", "her", "them", "this person"],
                    "personal_attack": ["they're not qualified", "they have a bias", "they're not credible"]
                }
            },
            {
                "template": "Either we {option1} or {option2}.",
                "fallacy_type": "false_dilemma",
                "variables": {
                    "option1": ["support this policy", "oppose this policy"],
                    "option2": ["destroy the economy", "ruin our society"]
                }
            },
            {
                "template": "If we allow {action1}, then {consequence1}, and if {consequence1}, then {consequence2}.",
                "fallacy_type": "slippery_slope",
                "variables": {
                    "action1": ["this change", "this policy", "this decision"],
                    "consequence1": ["society will collapse", "everything will fall apart", "chaos will ensue"],
                    "consequence2": ["we'll have anarchy", "civilization will end", "we'll lose everything"]
                }
            },
            {
                "template": "Everyone knows that {claim}.",
                "fallacy_type": "appeal_to_popularity",
                "variables": {
                    "claim": ["this is true", "this is obvious", "this is common sense"]
                }
            },
            {
                "template": "Dr. {expert} says {claim}, so it must be true.",
                "fallacy_type": "appeal_to_authority",
                "variables": {
                    "expert": ["Smith", "Johnson", "Williams"],
                    "claim": ["this is correct", "this is proven", "this is fact"]
                }
            }
        ]
    
    def _load_multilingual_templates(self) -> List[Dict[str, Any]]:
        """Load templates for multilingual content"""
        return [
            {
                "language": "es",
                "template": "La {entity} es {attribute} y {description}.",
                "translation": "The {entity} is {attribute} and {description}.",
                "variables": {
                    "entity": ["Tierra", "ciencia", "tecnología", "sociedad"],
                    "attribute": ["importante", "crucial", "esencial", "fundamental"],
                    "description": ["necesaria para el desarrollo", "vital para el progreso", "clave para el futuro"]
                }
            },
            {
                "language": "fr",
                "template": "Le {entity} est {attribute} et {description}.",
                "translation": "The {entity} is {attribute} and {description}.",
                "variables": {
                    "entity": ["monde", "changement", "développement", "avenir"],
                    "attribute": ["important", "crucial", "essentiel", "fondamental"],
                    "description": ["nécessaire pour le progrès", "vital pour l'avenir", "clé pour le développement"]
                }
            },
            {
                "language": "de",
                "template": "Die {entity} ist {attribute} und {description}.",
                "translation": "The {entity} is {attribute} and {description}.",
                "variables": {
                    "entity": ["Welt", "Wissenschaft", "Technologie", "Gesellschaft"],
                    "attribute": ["wichtig", "entscheidend", "wesentlich", "grundlegend"],
                    "description": ["notwendig für die Entwicklung", "wichtig für den Fortschritt", "entscheidend für die Zukunft"]
                }
            }
        ]
    
    def generate_claims(
        self,
        data_type: DataType,
        num_claims: int = 10,
        language: str = "en"
    ) -> List[SyntheticClaim]:
        """Generate synthetic claims of the specified type"""
        if data_type == DataType.TRUE_CLAIMS:
            templates = self.true_claim_templates
        elif data_type == DataType.FALSE_CLAIMS:
            templates = self.false_claim_templates
        elif data_type == DataType.MIXED_CLAIMS:
            templates = self.mixed_claim_templates
        elif data_type == DataType.UNVERIFIABLE_CLAIMS:
            templates = self.unverifiable_claim_templates
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
        
        claims = []
        for _ in range(num_claims):
            template_data = random.choice(templates)
            text = self._fill_template(template_data["template"], template_data["variables"])
            
            claim = SyntheticClaim(
                text=text,
                verdict=self._get_verdict_for_type(data_type),
                confidence=template_data.get("confidence", 0.8),
                category=template_data.get("category", "general"),
                language=language,
                metadata={
                    "template_id": templates.index(template_data),
                    "generated_at": datetime.now().isoformat(),
                    "data_type": data_type.value
                }
            )
            claims.append(claim)
        
        return claims
    
    def generate_evidence(
        self,
        num_evidence: int = 20,
        source_types: List[str] = None
    ) -> List[SyntheticEvidence]:
        """Generate synthetic evidence"""
        if source_types is None:
            source_types = ["academic", "news", "expert"]
        
        evidence = []
        for _ in range(num_evidence):
            template_data = random.choice(self.evidence_templates)
            
            if template_data["source_type"] not in source_types:
                continue
            
            source = self._fill_template(template_data["source"], template_data["variables"])
            title = self._fill_template(template_data["title"], template_data["variables"])
            snippet = self._fill_template(template_data["snippet"], template_data["variables"])
            
            # Generate realistic score based on reliability
            base_score = template_data["reliability"]
            score = base_score + random.uniform(-0.1, 0.1)
            score = max(0.0, min(1.0, score))
            
            evidence_item = SyntheticEvidence(
                source=source,
                title=title,
                snippet=snippet,
                score=score,
                source_type=template_data["source_type"],
                reliability=template_data["reliability"],
                metadata={
                    "template_id": self.evidence_templates.index(template_data),
                    "generated_at": datetime.now().isoformat()
                }
            )
            evidence.append(evidence_item)
        
        return evidence
    
    def generate_fallacies(
        self,
        num_fallacies: int = 15
    ) -> List[Dict[str, Any]]:
        """Generate synthetic logical fallacies"""
        fallacies = []
        for _ in range(num_fallacies):
            template_data = random.choice(self.fallacy_templates)
            text = self._fill_template(template_data["template"], template_data["variables"])
            
            fallacy = {
                "text": text,
                "type": template_data["fallacy_type"],
                "explanation": self._get_fallacy_explanation(template_data["fallacy_type"]),
                "confidence": random.uniform(0.7, 0.95),
                "severity": self._get_fallacy_severity(template_data["fallacy_type"]),
                "metadata": {
                    "template_id": self.fallacy_templates.index(template_data),
                    "generated_at": datetime.now().isoformat()
                }
            }
            fallacies.append(fallacy)
        
        return fallacies
    
    def generate_multilingual_content(
        self,
        target_language: str,
        num_content: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate multilingual content"""
        # Find templates for target language
        language_templates = [
            t for t in self.multilingual_templates 
            if t["language"] == target_language
        ]
        
        if not language_templates:
            raise ValueError(f"No templates available for language: {target_language}")
        
        content = []
        for _ in range(num_content):
            template_data = random.choice(language_templates)
            text = self._fill_template(template_data["template"], template_data["variables"])
            translation = self._fill_template(template_data["translation"], template_data["variables"])
            
            content_item = {
                "text": text,
                "translation": translation,
                "language": target_language,
                "confidence": random.uniform(0.8, 0.95),
                "metadata": {
                    "template_id": language_templates.index(template_data),
                    "generated_at": datetime.now().isoformat()
                }
            }
            content.append(content_item)
        
        return content
    
    def _fill_template(self, template: str, variables: Dict[str, List[str]]) -> str:
        """Fill template with random variable values"""
        result = template
        for var_name, var_values in variables.items():
            value = random.choice(var_values)
            result = result.replace(f"{{{var_name}}}", value)
        return result
    
    def _get_verdict_for_type(self, data_type: DataType) -> str:
        """Get verdict string for data type"""
        verdicts = {
            DataType.TRUE_CLAIMS: "true",
            DataType.FALSE_CLAIMS: "false",
            DataType.MIXED_CLAIMS: "mixed",
            DataType.UNVERIFIABLE_CLAIMS: "unverifiable"
        }
        return verdicts.get(data_type, "unknown")
    
    def _get_fallacy_explanation(self, fallacy_type: str) -> str:
        """Get explanation for fallacy type"""
        explanations = {
            "ad_hominem": "Attacking the person instead of the argument",
            "false_dilemma": "Presenting only two options when more exist",
            "slippery_slope": "Assuming a chain of events without evidence",
            "appeal_to_popularity": "Using popularity as evidence of truth",
            "appeal_to_authority": "Using authority as evidence without expertise"
        }
        return explanations.get(fallacy_type, "Logical fallacy detected")
    
    def _get_fallacy_severity(self, fallacy_type: str) -> str:
        """Get severity for fallacy type"""
        severities = {
            "ad_hominem": "high",
            "false_dilemma": "medium",
            "slippery_slope": "medium",
            "appeal_to_popularity": "low",
            "appeal_to_authority": "low"
        }
        return severities.get(fallacy_type, "medium")
    
    def generate_test_dataset(
        self,
        num_true: int = 50,
        num_false: int = 50,
        num_mixed: int = 25,
        num_unverifiable: int = 25,
        languages: List[str] = None
    ) -> Dict[str, Any]:
        """Generate a complete test dataset"""
        if languages is None:
            languages = ["en"]
        
        dataset = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_claims": num_true + num_false + num_mixed + num_unverifiable,
                "languages": languages,
                "generator_version": "1.0.0"
            },
            "claims": [],
            "evidence": [],
            "fallacies": []
        }
        
        # Generate claims for each language
        for language in languages:
            # True claims
            true_claims = self.generate_claims(DataType.TRUE_CLAIMS, num_true, language)
            dataset["claims"].extend(true_claims)
            
            # False claims
            false_claims = self.generate_claims(DataType.FALSE_CLAIMS, num_false, language)
            dataset["claims"].extend(false_claims)
            
            # Mixed claims
            mixed_claims = self.generate_claims(DataType.MIXED_CLAIMS, num_mixed, language)
            dataset["claims"].extend(mixed_claims)
            
            # Unverifiable claims
            unverifiable_claims = self.generate_claims(DataType.UNVERIFIABLE_CLAIMS, num_unverifiable, language)
            dataset["claims"].extend(unverifiable_claims)
        
        # Generate evidence
        dataset["evidence"] = self.generate_evidence(100)
        
        # Generate fallacies
        dataset["fallacies"] = self.generate_fallacies(50)
        
        return dataset
    
    def export_dataset(self, dataset: Dict[str, Any], filename: str):
        """Export dataset to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=2, ensure_ascii=False)
            logger.info(f"Dataset exported to {filename}")
        except Exception as e:
            logger.error(f"Error exporting dataset: {e}")
            raise






