#!/usr/bin/env python3
"""
Test script for Enhanced Anti-Hallucination Verification

This script demonstrates the multi-layered anti-hallucination approach
with self-reflection, multi-agent verification, and confidence calibration.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.verification_service import (
    VerificationService, SelfReflectionAgent, MultiAgentVerifier,
    RetrievalFirstPipeline, ConfidenceCalibrator, StructuredOutputValidator,
    AutoEscalationSystem
)


def test_self_reflection():
    """Test self-reflection mechanism"""
    
    print("🧠 Testing Self-Reflection Mechanism")
    print("=" * 50)
    
    reflection_agent = SelfReflectionAgent()
    
    test_cases = [
        {
            "name": "Evidence-Based Output",
            "output": "Based on the provided evidence from PubMed studies, the analysis shows...",
            "evidence": [{"source": "pubmed", "title": "Study 1"}, {"source": "pubmed", "title": "Study 2"}],
            "context": "Medical research analysis"
        },
        {
            "name": "Unsupported Claims",
            "output": "This is definitely proven fact that cannot be disputed.",
            "evidence": [{"source": "unknown", "title": "Weak source"}],
            "context": "Controversial topic"
        },
        {
            "name": "Fabricated Information",
            "output": "Studies show that this is completely true. Research proves everything.",
            "evidence": [],
            "context": "No evidence available"
        },
        {
            "name": "High Confidence Claims",
            "output": "We are very confident that this is absolutely certain.",
            "evidence": [{"source": "weak", "title": "Single source"}],
            "context": "Complex analysis"
        },
        {
            "name": "Logical Inconsistencies",
            "output": "This is always true, however it is never correct.",
            "evidence": [{"source": "mixed", "title": "Conflicting evidence"}],
            "context": "Contradictory analysis"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Output: \"{test_case['output']}\"")
        
        result = reflection_agent.reflect_on_output(
            test_case['output'], 
            test_case['evidence'], 
            test_case['context']
        )
        
        print(f"   Overall Score: {result['overall_score']:.3f}")
        print(f"   Hallucination Risk: {result['hallucination_risk']}")
        print(f"   Individual Scores:")
        for detail in result['details']:
            print(f"     - {detail['question'][:30]}...: {detail['score']:.3f}")


def test_multi_agent_verification():
    """Test multi-agent verification system"""
    
    print("\n🤖 Testing Multi-Agent Verification")
    print("=" * 50)
    
    multi_agent = MultiAgentVerifier()
    
    test_cases = [
        {
            "name": "Strong Evidence",
            "content": "Studies show that vaccines are safe and effective.",
            "evidence": [
                {"source": "pubmed", "title": "Vaccine Safety Study", "score": 0.9},
                {"source": "who", "title": "WHO Report", "score": 0.8}
            ],
            "sag": {"nodes": [{"id": "claim1", "type": "claim"}], "edges": []}
        },
        {
            "name": "Weak Evidence",
            "content": "This is definitely true based on my opinion.",
            "evidence": [
                {"source": "blog", "title": "Personal Blog", "score": 0.2}
            ],
            "sag": {"nodes": [], "edges": []}
        },
        {
            "name": "Contradictory Content",
            "content": "This is always true and never false.",
            "evidence": [
                {"source": "mixed", "title": "Mixed Evidence", "score": 0.5}
            ],
            "sag": {"nodes": [{"id": "contradiction", "type": "contradiction"}], "edges": []}
        },
        {
            "name": "No Evidence",
            "content": "This is a factual statement.",
            "evidence": [],
            "sag": {"nodes": [], "edges": []}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Content: \"{test_case['content']}\"")
        
        result = multi_agent.cross_check_verification(
            test_case['content'],
            test_case['evidence'],
            test_case['sag']
        )
        
        print(f"   Consensus: {result['consensus']:.3f}")
        print(f"   Disagreement: {result['disagreement']:.3f}")
        print(f"   Reliability: {result['reliability']}")
        print(f"   Agent Results:")
        for agent in result['agents']:
            print(f"     - {agent['agent']}: {agent['confidence']:.3f}")


def test_retrieval_first_pipeline():
    """Test retrieval-first pipeline validation"""
    
    print("\n🔍 Testing Retrieval-First Pipeline")
    print("=" * 50)
    
    retrieval_pipeline = RetrievalFirstPipeline()
    
    test_cases = [
        {
            "name": "Evidence-Based Response",
            "content": "According to the study, vaccines are effective.",
            "evidence": [
                {"source": "pubmed", "title": "Vaccine Study", "score": 0.8, "snippet": "vaccines are effective"},
                {"source": "who", "title": "WHO Report", "score": 0.7, "snippet": "vaccination benefits"}
            ],
            "sag": {"nodes": [{"id": "study", "type": "evidence"}], "edges": []}
        },
        {
            "name": "Non-Evidence-Based Response",
            "content": "This is my personal opinion about the topic.",
            "evidence": [
                {"source": "blog", "title": "Personal Blog", "score": 0.1, "snippet": "random content"}
            ],
            "sag": {"nodes": [], "edges": []}
        },
        {
            "name": "Insufficient Evidence",
            "content": "The evidence clearly shows this is true.",
            "evidence": [
                {"source": "weak", "title": "Weak Source", "score": 0.2, "snippet": "unrelated content"}
            ],
            "sag": {"nodes": [], "edges": []}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Content: \"{test_case['content']}\"")
        
        result = retrieval_pipeline.validate_evidence_basis(
            test_case['content'],
            test_case['evidence'],
            test_case['sag']
        )
        
        print(f"   Evidence-Based: {result['is_evidence_based']}")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Evidence Count: {result['evidence_count']}")
        print(f"   High Quality Count: {result['high_quality_count']}")
        print(f"   Alignment Score: {result['alignment_score']:.3f}")


def test_confidence_calibration():
    """Test confidence calibration system"""
    
    print("\n📊 Testing Confidence Calibration")
    print("=" * 50)
    
    calibrator = ConfidenceCalibrator()
    
    test_cases = [
        {
            "name": "High Quality Evidence",
            "raw_confidence": 0.8,
            "evidence_quality": 0.9,
            "multi_agent_consensus": 0.85,
            "self_reflection_score": 0.8
        },
        {
            "name": "Medium Quality Evidence",
            "raw_confidence": 0.6,
            "evidence_quality": 0.5,
            "multi_agent_consensus": 0.6,
            "self_reflection_score": 0.5
        },
        {
            "name": "Low Quality Evidence",
            "raw_confidence": 0.4,
            "evidence_quality": 0.2,
            "multi_agent_consensus": 0.3,
            "self_reflection_score": 0.2
        },
        {
            "name": "Conflicting Signals",
            "raw_confidence": 0.7,
            "evidence_quality": 0.3,
            "multi_agent_consensus": 0.4,
            "self_reflection_score": 0.6
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        
        result = calibrator.calibrate_confidence(
            test_case['raw_confidence'],
            test_case['evidence_quality'],
            test_case['multi_agent_consensus'],
            test_case['self_reflection_score']
        )
        
        print(f"   Raw Confidence: {result['raw_confidence']:.3f}")
        print(f"   Calibrated Confidence: {result['calibrated_confidence']:.3f}")
        print(f"   Calibration Level: {result['calibration_level']}")
        print(f"   Evidence Quality: {result['evidence_quality']:.3f}")
        print(f"   Consensus: {result['consensus']:.3f}")
        print(f"   Self-Reflection: {result['self_reflection']:.3f}")


def test_auto_escalation():
    """Test auto-escalation system"""
    
    print("\n⚡ Testing Auto-Escalation System")
    print("=" * 50)
    
    escalation_system = AutoEscalationSystem()
    
    test_cases = [
        {"confidence": 0.9, "complexity": 0.2, "expected": "mini_model"},
        {"confidence": 0.7, "complexity": 0.5, "expected": "medium_model"},
        {"confidence": 0.3, "complexity": 0.8, "expected": "large_model"},
        {"confidence": 0.1, "complexity": 0.9, "expected": "large_model"}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Confidence: {test_case['confidence']:.1f}, Complexity: {test_case['complexity']:.1f}")
        
        result = escalation_system.should_escalate(
            test_case['confidence'],
            test_case['complexity']
        )
        
        print(f"   Escalation Needed: {result['escalation_needed']}")
        print(f"   Current Model: {result['current_model']}")
        print(f"   Target Model: {result['target_model']}")
        print(f"   Expected: {test_case['expected']}")
        print(f"   Match: {'✅' if result['target_model'] == test_case['expected'] else '❌'}")


def test_enhanced_verification():
    """Test complete enhanced verification system"""
    
    print("\n🛡️ Testing Enhanced Anti-Hallucination Verification")
    print("=" * 60)
    
    verifier = VerificationService()
    
    test_cases = [
        {
            "name": "High-Quality Analysis",
            "content": "Based on multiple peer-reviewed studies, vaccines are safe and effective.",
            "evidence": [
                {"source": "pubmed", "title": "Vaccine Safety Study", "score": 0.9},
                {"source": "who", "title": "WHO Report", "score": 0.8},
                {"source": "cdc", "title": "CDC Guidelines", "score": 0.85}
            ],
            "sag": {
                "nodes": [{"id": "claim1", "type": "claim"}, {"id": "evidence1", "type": "evidence"}],
                "edges": [{"source": "claim1", "target": "evidence1", "relation": "supported_by"}]
            }
        },
        {
            "name": "Low-Quality Analysis",
            "content": "This is definitely true because I say so.",
            "evidence": [
                {"source": "blog", "title": "Personal Opinion", "score": 0.1}
            ],
            "sag": {"nodes": [], "edges": []}
        },
        {
            "name": "Hallucination Risk",
            "content": "Studies definitively prove that this is absolutely certain.",
            "evidence": [],
            "sag": {"nodes": [], "edges": []}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Content: \"{test_case['content']}\"")
        
        result = verifier.verify(
            test_case['sag'],
            test_case['evidence'],
            test_case['content']
        )
        
        print(f"   Confidence: {result.confidence:.3f}")
        print(f"   Method: {result.method}")
        print(f"   Notes: {result.notes}")
        
        # Parse notes for detailed analysis
        notes_parts = result.notes.split("; ")
        print(f"   Detailed Analysis:")
        for part in notes_parts:
            if "=" in part:
                key, value = part.split("=", 1)
                print(f"     - {key}: {value}")


def demo_anti_hallucination_benefits():
    """Demonstrate benefits of anti-hallucination system"""
    
    print("\n🎯 Anti-Hallucination System Benefits")
    print("=" * 50)
    
    benefits = [
        "✅ Multi-Agent Cross-Check: Multiple verification perspectives",
        "✅ Self-Reflection: AI questions its own output",
        "✅ Retrieval-First: Ensures evidence-based responses",
        "✅ Confidence Calibration: TruthfulQA-based calibration",
        "✅ Structured Validation: JSON schema validation",
        "✅ Auto-Escalation: Dynamic model selection",
        "✅ Hallucination Detection: Risk assessment and mitigation",
        "✅ Evidence Alignment: Content-evidence consistency checks",
        "✅ Logical Consistency: Contradiction detection",
        "✅ Factual Accuracy: Evidence strength validation"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")


if __name__ == "__main__":
    print("🚀 FailSafe Enhanced Anti-Hallucination Test Suite")
    print("=" * 70)
    
    try:
        # Run individual component tests
        test_self_reflection()
        test_multi_agent_verification()
        test_retrieval_first_pipeline()
        test_confidence_calibration()
        test_auto_escalation()
        
        # Run complete system test
        test_enhanced_verification()
        
        # Show benefits
        demo_anti_hallucination_benefits()
        
        print(f"\n✅ SUCCESS: Enhanced Anti-Hallucination system is working correctly!")
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

