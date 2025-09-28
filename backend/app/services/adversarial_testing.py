"""
Adversarial Testing Framework for FailSafe
Tests system robustness against various attacks and edge cases
"""

import asyncio
import random
import string
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AttackType(Enum):
    """Types of adversarial attacks to test"""
    NOISE_INJECTION = "noise_injection"
    SEMANTIC_PERTURBATION = "semantic_perturbation"
    LOGICAL_MANIPULATION = "logical_manipulation"
    EVIDENCE_POISONING = "evidence_poisoning"
    CONFIDENCE_ATTACK = "confidence_attack"
    MULTILINGUAL_ATTACK = "multilingual_attack"
    CONTEXT_MANIPULATION = "context_manipulation"

@dataclass
class AttackResult:
    """Result of an adversarial attack test"""
    attack_type: AttackType
    original_text: str
    modified_text: str
    original_verdict: str
    modified_verdict: str
    original_confidence: float
    modified_confidence: float
    success: bool
    robustness_score: float
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class TestSuite:
    """Collection of test cases for adversarial testing"""
    name: str
    description: str
    test_cases: List[Dict[str, Any]]
    expected_robustness: float
    metadata: Dict[str, Any]

class NoiseInjector:
    """Inject various types of noise into text"""
    
    @staticmethod
    def character_noise(text: str, noise_level: float = 0.1) -> str:
        """Add character-level noise (typos, substitutions)"""
        if noise_level <= 0:
            return text
        
        chars = list(text)
        num_changes = int(len(chars) * noise_level)
        
        for _ in range(num_changes):
            if not chars:
                break
                
            pos = random.randint(0, len(chars) - 1)
            char = chars[pos]
            
            if char.isalpha():
                # Character substitution
                if random.random() < 0.5:
                    chars[pos] = random.choice(string.ascii_letters)
                # Character deletion
                elif random.random() < 0.3:
                    chars.pop(pos)
                # Character insertion
                else:
                    chars.insert(pos, random.choice(string.ascii_letters))
        
        return ''.join(chars)
    
    @staticmethod
    def word_noise(text: str, noise_level: float = 0.1) -> str:
        """Add word-level noise (word substitutions, insertions, deletions)"""
        if noise_level <= 0:
            return text
        
        words = text.split()
        num_changes = int(len(words) * noise_level)
        
        # Word substitutions
        substitutions = {
            'the': ['a', 'an', 'some'],
            'is': ['are', 'was', 'were'],
            'and': ['or', 'but', 'yet'],
            'not': ['never', 'no', 'none'],
            'very': ['extremely', 'highly', 'quite'],
            'good': ['great', 'excellent', 'wonderful'],
            'bad': ['terrible', 'awful', 'horrible'],
            'big': ['large', 'huge', 'enormous'],
            'small': ['tiny', 'little', 'miniature']
        }
        
        for _ in range(num_changes):
            if not words:
                break
                
            pos = random.randint(0, len(words) - 1)
            word = words[pos].lower().strip('.,!?;:')
            
            if word in substitutions:
                words[pos] = random.choice(substitutions[word])
            elif random.random() < 0.3:
                # Random word insertion
                words.insert(pos, random.choice(list(substitutions.keys())))
            elif random.random() < 0.2:
                # Word deletion
                words.pop(pos)
        
        return ' '.join(words)
    
    @staticmethod
    def punctuation_noise(text: str, noise_level: float = 0.1) -> str:
        """Add punctuation noise"""
        if noise_level <= 0:
            return text
        
        chars = list(text)
        num_changes = int(len(chars) * noise_level)
        
        for _ in range(num_changes):
            if not chars:
                break
                
            pos = random.randint(0, len(chars) - 1)
            
            if random.random() < 0.5:
                # Add random punctuation
                chars.insert(pos, random.choice('.,!?;:'))
            else:
                # Remove punctuation
                if chars[pos] in '.,!?;:':
                    chars.pop(pos)
        
        return ''.join(chars)

class SemanticPerturbator:
    """Perturb text while maintaining semantic meaning"""
    
    @staticmethod
    def synonym_replacement(text: str, replacement_rate: float = 0.3) -> str:
        """Replace words with synonyms"""
        synonyms = {
            'good': ['excellent', 'great', 'wonderful', 'fantastic'],
            'bad': ['terrible', 'awful', 'horrible', 'dreadful'],
            'big': ['large', 'huge', 'enormous', 'massive'],
            'small': ['tiny', 'little', 'miniature', 'petite'],
            'fast': ['quick', 'rapid', 'swift', 'speedy'],
            'slow': ['sluggish', 'lethargic', 'sluggish', 'tardy'],
            'important': ['crucial', 'vital', 'essential', 'critical'],
            'difficult': ['challenging', 'hard', 'tough', 'arduous'],
            'easy': ['simple', 'straightforward', 'effortless', 'uncomplicated'],
            'beautiful': ['gorgeous', 'stunning', 'lovely', 'attractive']
        }
        
        words = text.split()
        for i, word in enumerate(words):
            word_lower = word.lower().strip('.,!?;:')
            if word_lower in synonyms and random.random() < replacement_rate:
                words[i] = random.choice(synonyms[word_lower])
        
        return ' '.join(words)
    
    @staticmethod
    def sentence_reordering(text: str) -> str:
        """Reorder sentences while maintaining coherence"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 1:
            return text
        
        # Keep first and last sentences in place for coherence
        if len(sentences) > 2:
            middle = sentences[1:-1]
            random.shuffle(middle)
            sentences = [sentences[0]] + middle + [sentences[-1]]
        
        return '. '.join(sentences) + '.'
    
    @staticmethod
    def passive_to_active(text: str) -> str:
        """Convert passive voice to active voice"""
        # Simple passive to active conversion patterns
        patterns = [
            (r'is (.*?) by', r'\1'),
            (r'was (.*?) by', r'\1'),
            (r'are (.*?) by', r'\1'),
            (r'were (.*?) by', r'\1'),
            (r'been (.*?) by', r'\1'),
        ]
        
        modified_text = text
        for pattern, replacement in patterns:
            modified_text = re.sub(pattern, replacement, modified_text, flags=re.IGNORECASE)
        
        return modified_text

class LogicalManipulator:
    """Manipulate logical structure of arguments"""
    
    @staticmethod
    def add_false_premises(text: str, num_premises: int = 2) -> str:
        """Add false premises to make argument seem stronger"""
        false_premises = [
            "Studies have shown that",
            "Research indicates that",
            "Experts agree that",
            "It is well-known that",
            "Statistics prove that",
            "Data shows that",
            "Evidence suggests that",
            "Analysis reveals that"
        ]
        
        sentences = text.split('.')
        if len(sentences) < 2:
            return text
        
        # Insert false premises at random positions
        for _ in range(min(num_premises, len(sentences) - 1)):
            pos = random.randint(1, len(sentences) - 1)
            premise = random.choice(false_premises)
            sentences.insert(pos, f"{premise} this is true.")
        
        return '. '.join(sentences)
    
    @staticmethod
    def create_circular_reasoning(text: str) -> str:
        """Create circular reasoning patterns"""
        # Extract main claim
        sentences = text.split('.')
        if not sentences:
            return text
        
        main_claim = sentences[0].strip()
        if not main_claim:
            return text
        
        # Add circular reasoning
        circular_additions = [
            f"This is true because {main_claim.lower()}.",
            f"The evidence for this is that {main_claim.lower()}.",
            f"This proves that {main_claim.lower()} is correct."
        ]
        
        # Insert circular reasoning
        for addition in circular_additions:
            sentences.insert(1, addition)
        
        return '. '.join(sentences)
    
    @staticmethod
    def add_straw_man(text: str) -> str:
        """Add straw man arguments"""
        straw_man_phrases = [
            "Some people might say that",
            "Critics argue that",
            "Opponents claim that",
            "Detractors suggest that",
            "Skeptics believe that"
        ]
        
        counter_arguments = [
            "but this is clearly wrong because",
            "however, this is not true since",
            "but this is a misunderstanding because",
            "however, this is incorrect as",
            "but this is false because"
        ]
        
        sentences = text.split('.')
        if len(sentences) < 2:
            return text
        
        # Add straw man argument
        straw_man = random.choice(straw_man_phrases)
        counter = random.choice(counter_arguments)
        
        # Insert after first sentence
        sentences.insert(1, f"{straw_man} this is wrong. {counter} the evidence shows otherwise.")
        
        return '. '.join(sentences)

class EvidencePoisoner:
    """Poison evidence to test retrieval robustness"""
    
    @staticmethod
    def add_fake_sources(text: str, num_sources: int = 3) -> str:
        """Add fake source references"""
        fake_sources = [
            "According to a study by Harvard University",
            "Research from MIT shows that",
            "A report from Stanford indicates",
            "Studies from Oxford University prove",
            "Data from Cambridge University reveals",
            "Analysis from Yale University suggests",
            "Findings from Princeton University show",
            "Research from Caltech demonstrates"
        ]
        
        sentences = text.split('.')
        if not sentences:
            return text
        
        # Add fake sources
        for _ in range(min(num_sources, len(sentences))):
            pos = random.randint(0, len(sentences) - 1)
            source = random.choice(fake_sources)
            sentences[pos] = f"{source}, {sentences[pos].strip()}"
        
        return '. '.join(sentences)
    
    @staticmethod
    def add_biased_quotes(text: str) -> str:
        """Add biased or misleading quotes"""
        biased_quotes = [
            '"This is definitely true" - Expert',
            '"The evidence is overwhelming" - Scientist',
            '"This is beyond doubt" - Researcher',
            '"The data is conclusive" - Analyst',
            '"This is irrefutable" - Specialist'
        ]
        
        sentences = text.split('.')
        if not sentences:
            return text
        
        # Add biased quotes
        for quote in biased_quotes:
            pos = random.randint(0, len(sentences) - 1)
            sentences[pos] = f"{sentences[pos].strip()} {quote}"
        
        return '. '.join(sentences)

class ConfidenceAttacker:
    """Attack confidence calibration"""
    
    @staticmethod
    def add_confidence_boosters(text: str) -> str:
        """Add phrases that artificially boost confidence"""
        boosters = [
            "It is absolutely certain that",
            "There is no doubt that",
            "It is completely clear that",
            "It is undeniably true that",
            "It is irrefutable that",
            "It is beyond question that",
            "It is indisputable that",
            "It is unquestionably true that"
        ]
        
        sentences = text.split('.')
        if not sentences:
            return text
        
        # Add confidence boosters
        for booster in boosters:
            pos = random.randint(0, len(sentences) - 1)
            sentences[pos] = f"{booster} {sentences[pos].strip()}"
        
        return '. '.join(sentences)
    
    @staticmethod
    def add_uncertainty_phrases(text: str) -> str:
        """Add phrases that reduce confidence"""
        uncertainty_phrases = [
            "It might be possible that",
            "There could be a chance that",
            "It is possible that",
            "Perhaps",
            "Maybe",
            "It seems like",
            "It appears that",
            "It looks like"
        ]
        
        sentences = text.split('.')
        if not sentences:
            return text
        
        # Add uncertainty phrases
        for phrase in uncertainty_phrases:
            pos = random.randint(0, len(sentences) - 1)
            sentences[pos] = f"{phrase} {sentences[pos].strip()}"
        
        return '. '.join(sentences)

class MultilingualAttacker:
    """Attack multilingual processing"""
    
    @staticmethod
    def code_switching(text: str, target_language: str = "es") -> str:
        """Add code-switching between languages"""
        translations = {
            "es": {
                "the": "el", "and": "y", "is": "es", "are": "son",
                "good": "bueno", "bad": "malo", "true": "verdadero",
                "false": "falso", "important": "importante"
            },
            "fr": {
                "the": "le", "and": "et", "is": "est", "are": "sont",
                "good": "bon", "bad": "mauvais", "true": "vrai",
                "false": "faux", "important": "important"
            }
        }
        
        if target_language not in translations:
            return text
        
        words = text.split()
        for i, word in enumerate(words):
            word_lower = word.lower().strip('.,!?;:')
            if word_lower in translations[target_language]:
                if random.random() < 0.3:  # 30% chance of switching
                    words[i] = translations[target_language][word_lower]
        
        return ' '.join(words)
    
    @staticmethod
    def add_foreign_characters(text: str) -> str:
        """Add foreign characters that might confuse processing"""
        foreign_chars = "àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ"
        
        chars = list(text)
        for i, char in enumerate(chars):
            if char.isalpha() and random.random() < 0.1:
                chars[i] = random.choice(foreign_chars)
        
        return ''.join(chars)

class ContextManipulator:
    """Manipulate context to test robustness"""
    
    @staticmethod
    def add_irrelevant_context(text: str, context_length: int = 100) -> str:
        """Add irrelevant context that might confuse the system"""
        irrelevant_contexts = [
            "The weather today is sunny and warm. ",
            "I had a great breakfast this morning. ",
            "The traffic was terrible on my way to work. ",
            "My favorite color is blue. ",
            "I love listening to music. ",
            "The stock market is doing well today. ",
            "I need to buy groceries later. ",
            "My dog is very cute. "
        ]
        
        # Add random irrelevant context
        context = ''.join(random.choices(irrelevant_contexts, k=context_length // 20))
        return context + text
    
    @staticmethod
    def add_emotional_context(text: str) -> str:
        """Add emotional context that might bias analysis"""
        emotional_prefixes = [
            "This is absolutely outrageous! ",
            "I can't believe this is happening! ",
            "This is so frustrating! ",
            "I'm really excited about this! ",
            "This is incredibly important! ",
            "I'm deeply concerned about this! ",
            "This is truly amazing! ",
            "I'm shocked by this! "
        ]
        
        prefix = random.choice(emotional_prefixes)
        return prefix + text

class AdversarialTester:
    """Main class for running adversarial tests"""
    
    def __init__(self):
        self.noise_injector = NoiseInjector()
        self.semantic_perturbator = SemanticPerturbator()
        self.logical_manipulator = LogicalManipulator()
        self.evidence_poisoner = EvidencePoisoner()
        self.confidence_attacker = ConfidenceAttacker()
        self.multilingual_attacker = MultilingualAttacker()
        self.context_manipulator = ContextManipulator()
    
    async def run_attack(
        self,
        attack_type: AttackType,
        text: str,
        analysis_service: Any,
        **kwargs
    ) -> AttackResult:
        """Run a single adversarial attack"""
        try:
            # Get original analysis
            original_result = await analysis_service.analyze_claim(text)
            original_verdict = original_result.get('verdict', 'unknown')
            original_confidence = original_result.get('confidence', 0.0)
            
            # Apply attack
            modified_text = self._apply_attack(attack_type, text, **kwargs)
            
            # Get modified analysis
            modified_result = await analysis_service.analyze_claim(modified_text)
            modified_verdict = modified_result.get('verdict', 'unknown')
            modified_confidence = modified_result.get('confidence', 0.0)
            
            # Calculate robustness score
            robustness_score = self._calculate_robustness_score(
                original_verdict, modified_verdict,
                original_confidence, modified_confidence
            )
            
            # Determine if attack was successful
            success = self._is_attack_successful(
                original_verdict, modified_verdict,
                original_confidence, modified_confidence
            )
            
            return AttackResult(
                attack_type=attack_type,
                original_text=text,
                modified_text=modified_text,
                original_verdict=original_verdict,
                modified_verdict=modified_verdict,
                original_confidence=original_confidence,
                modified_confidence=modified_confidence,
                success=success,
                robustness_score=robustness_score,
                metadata=kwargs,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error running attack {attack_type}: {e}")
            return AttackResult(
                attack_type=attack_type,
                original_text=text,
                modified_text=text,
                original_verdict="error",
                modified_verdict="error",
                original_confidence=0.0,
                modified_confidence=0.0,
                success=False,
                robustness_score=0.0,
                metadata={"error": str(e)},
                timestamp=datetime.now()
            )
    
    def _apply_attack(self, attack_type: AttackType, text: str, **kwargs) -> str:
        """Apply the specified attack to the text"""
        if attack_type == AttackType.NOISE_INJECTION:
            noise_level = kwargs.get('noise_level', 0.1)
            return self.noise_injector.character_noise(text, noise_level)
        
        elif attack_type == AttackType.SEMANTIC_PERTURBATION:
            replacement_rate = kwargs.get('replacement_rate', 0.3)
            return self.semantic_perturbator.synonym_replacement(text, replacement_rate)
        
        elif attack_type == AttackType.LOGICAL_MANIPULATION:
            num_premises = kwargs.get('num_premises', 2)
            return self.logical_manipulator.add_false_premises(text, num_premises)
        
        elif attack_type == AttackType.EVIDENCE_POISONING:
            num_sources = kwargs.get('num_sources', 3)
            return self.evidence_poisoner.add_fake_sources(text, num_sources)
        
        elif attack_type == AttackType.CONFIDENCE_ATTACK:
            if kwargs.get('boost', True):
                return self.confidence_attacker.add_confidence_boosters(text)
            else:
                return self.confidence_attacker.add_uncertainty_phrases(text)
        
        elif attack_type == AttackType.MULTILINGUAL_ATTACK:
            target_language = kwargs.get('target_language', 'es')
            return self.multilingual_attacker.code_switching(text, target_language)
        
        elif attack_type == AttackType.CONTEXT_MANIPULATION:
            context_length = kwargs.get('context_length', 100)
            return self.context_manipulator.add_irrelevant_context(text, context_length)
        
        else:
            return text
    
    def _calculate_robustness_score(
        self,
        original_verdict: str,
        modified_verdict: str,
        original_confidence: float,
        modified_confidence: float
    ) -> float:
        """Calculate robustness score (0-1, higher is better)"""
        # Verdict consistency (0.6 weight)
        verdict_consistent = 1.0 if original_verdict == modified_verdict else 0.0
        
        # Confidence stability (0.4 weight)
        confidence_diff = abs(original_confidence - modified_confidence)
        confidence_stable = max(0.0, 1.0 - confidence_diff)
        
        return 0.6 * verdict_consistent + 0.4 * confidence_stable
    
    def _is_attack_successful(
        self,
        original_verdict: str,
        modified_verdict: str,
        original_confidence: float,
        modified_confidence: float
    ) -> bool:
        """Determine if the attack was successful"""
        # Attack is successful if verdict changed or confidence changed significantly
        verdict_changed = original_verdict != modified_verdict
        confidence_changed = abs(original_confidence - modified_confidence) > 0.2
        
        return verdict_changed or confidence_changed
    
    async def run_test_suite(
        self,
        test_suite: TestSuite,
        analysis_service: Any
    ) -> List[AttackResult]:
        """Run a complete test suite"""
        results = []
        
        for test_case in test_suite.test_cases:
            attack_type = AttackType(test_case['attack_type'])
            text = test_case['text']
            kwargs = test_case.get('parameters', {})
            
            result = await self.run_attack(attack_type, text, analysis_service, **kwargs)
            results.append(result)
        
        return results
    
    def generate_synthetic_test_cases(self, num_cases: int = 100) -> TestSuite:
        """Generate synthetic test cases for comprehensive testing"""
        test_cases = []
        
        # Base test texts
        base_texts = [
            "The Earth is round and orbits around the Sun.",
            "Climate change is caused by human activities.",
            "Vaccines are safe and effective for preventing diseases.",
            "The COVID-19 pandemic has affected global economies.",
            "Artificial intelligence will transform many industries.",
            "Renewable energy sources are becoming more cost-effective.",
            "Social media has both positive and negative impacts on society.",
            "Education is essential for personal and societal development.",
            "Technology has improved healthcare outcomes significantly.",
            "Globalization has increased international trade and cooperation."
        ]
        
        # Attack types and their parameters
        attack_configs = [
            (AttackType.NOISE_INJECTION, {'noise_level': 0.1}),
            (AttackType.NOISE_INJECTION, {'noise_level': 0.2}),
            (AttackType.SEMANTIC_PERTURBATION, {'replacement_rate': 0.3}),
            (AttackType.SEMANTIC_PERTURBATION, {'replacement_rate': 0.5}),
            (AttackType.LOGICAL_MANIPULATION, {'num_premises': 2}),
            (AttackType.LOGICAL_MANIPULATION, {'num_premises': 4}),
            (AttackType.EVIDENCE_POISONING, {'num_sources': 3}),
            (AttackType.EVIDENCE_POISONING, {'num_sources': 5}),
            (AttackType.CONFIDENCE_ATTACK, {'boost': True}),
            (AttackType.CONFIDENCE_ATTACK, {'boost': False}),
            (AttackType.MULTILINGUAL_ATTACK, {'target_language': 'es'}),
            (AttackType.MULTILINGUAL_ATTACK, {'target_language': 'fr'}),
            (AttackType.CONTEXT_MANIPULATION, {'context_length': 100}),
            (AttackType.CONTEXT_MANIPULATION, {'context_length': 200})
        ]
        
        # Generate test cases
        for _ in range(num_cases):
            text = random.choice(base_texts)
            attack_type, parameters = random.choice(attack_configs)
            
            test_cases.append({
                'text': text,
                'attack_type': attack_type.value,
                'parameters': parameters
            })
        
        return TestSuite(
            name="Synthetic Adversarial Test Suite",
            description="Comprehensive test suite with synthetic data",
            test_cases=test_cases,
            expected_robustness=0.8,
            metadata={"generated": True, "num_cases": num_cases}
        )
    
    def analyze_results(self, results: List[AttackResult]) -> Dict[str, Any]:
        """Analyze test results and generate statistics"""
        if not results:
            return {"error": "No results to analyze"}
        
        total_tests = len(results)
        successful_attacks = sum(1 for r in results if r.success)
        attack_success_rate = successful_attacks / total_tests
        
        avg_robustness = np.mean([r.robustness_score for r in results])
        
        # Group by attack type
        by_attack_type = {}
        for result in results:
            attack_type = result.attack_type.value
            if attack_type not in by_attack_type:
                by_attack_type[attack_type] = []
            by_attack_type[attack_type].append(result)
        
        # Calculate statistics per attack type
        attack_type_stats = {}
        for attack_type, attack_results in by_attack_type.items():
            attack_type_stats[attack_type] = {
                'count': len(attack_results),
                'success_rate': sum(1 for r in attack_results if r.success) / len(attack_results),
                'avg_robustness': np.mean([r.robustness_score for r in attack_results]),
                'avg_confidence_change': np.mean([
                    abs(r.original_confidence - r.modified_confidence) 
                    for r in attack_results
                ])
            }
        
        return {
            'total_tests': total_tests,
            'successful_attacks': successful_attacks,
            'attack_success_rate': attack_success_rate,
            'avg_robustness': avg_robustness,
            'attack_type_stats': attack_type_stats,
            'overall_robustness_grade': self._get_robustness_grade(avg_robustness)
        }
    
    def _get_robustness_grade(self, robustness_score: float) -> str:
        """Convert robustness score to letter grade"""
        if robustness_score >= 0.9:
            return 'A'
        elif robustness_score >= 0.8:
            return 'B'
        elif robustness_score >= 0.7:
            return 'C'
        elif robustness_score >= 0.6:
            return 'D'
        else:
            return 'F'






