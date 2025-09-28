#!/usr/bin/env python3
"""
Test script for Advanced Fallacy Detection

This script demonstrates the enhanced fallacy detection capabilities
with various types of logical fallacies and their detection.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.fallacy_detector import FallacyDetector


def test_fallacy_detection():
    """Test fallacy detection with various examples"""
    
    detector = FallacyDetector()
    
    # Test cases with different types of fallacies
    test_cases = [
        {
            "name": "Hasty Generalization",
            "text": "All politicians are corrupt and always lie to the public.",
            "expected_fallacies": ["hasty_generalization"]
        },
        {
            "name": "Ad Hominem",
            "text": "You're an idiot if you believe that climate change is real.",
            "expected_fallacies": ["ad_hominem"]
        },
        {
            "name": "Straw Man",
            "text": "So you're saying that all vaccines are dangerous and should be banned?",
            "expected_fallacies": ["straw_man"]
        },
        {
            "name": "False Dilemma",
            "text": "You're either with us or against us in this war.",
            "expected_fallacies": ["false_dilemma"]
        },
        {
            "name": "Slippery Slope",
            "text": "If we allow same-sex marriage, then people will start marrying animals.",
            "expected_fallacies": ["slippery_slope"]
        },
        {
            "name": "Appeal to Authority",
            "text": "Dr. Smith says that this medicine works, so it must be true.",
            "expected_fallacies": ["appeal_to_authority"]
        },
        {
            "name": "Cherry Picking",
            "text": "Studies show that coffee is good for you, ignoring the fact that it can cause insomnia.",
            "expected_fallacies": ["cherry_picking"]
        },
        {
            "name": "Correlation vs Causation",
            "text": "Since ice cream sales increased, so did drowning incidents, therefore ice cream causes drowning.",
            "expected_fallacies": ["correlation_causation"]
        },
        {
            "name": "Appeal to Emotion",
            "text": "Think of the children! How can you not support this policy?",
            "expected_fallacies": ["appeal_to_emotion"]
        },
        {
            "name": "Red Herring",
            "text": "That's not the point. What about the economy?",
            "expected_fallacies": ["red_herring"]
        },
        {
            "name": "Complex Logical Structure",
            "text": "If we assume that the premise is true, then given that the evidence supports it, therefore we can conclude that the hypothesis is valid, since all the conditions are met.",
            "expected_fallacies": ["complex_logical_error", "argumentative_pattern"]
        },
        {
            "name": "Multiple Fallacies",
            "text": "You're stupid if you think that all scientists agree on climate change. So you're saying that every single scientist in the world believes the same thing? That's ridiculous!",
            "expected_fallacies": ["ad_hominem", "straw_man", "hasty_generalization"]
        },
        {
            "name": "No Fallacies",
            "text": "The evidence suggests that regular exercise can improve cardiovascular health based on multiple peer-reviewed studies.",
            "expected_fallacies": []
        }
    ]
    
    print("🧪 Testing Advanced Fallacy Detection System")
    print("=" * 60)
    
    total_tests = len(test_cases)
    passed_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Text: \"{test_case['text']}\"")
        
        # Detect fallacies
        detected_fallacies = detector.detect(test_case['text'])
        detected_types = [f.type for f in detected_fallacies]
        
        print(f"   Expected: {test_case['expected_fallacies']}")
        print(f"   Detected: {detected_types}")
        
        # Check if detection matches expectations
        expected_set = set(test_case['expected_fallacies'])
        detected_set = set(detected_types)
        
        if expected_set == detected_set:
            print("   ✅ PASS")
            passed_tests += 1
        else:
            print("   ❌ FAIL")
            if expected_set - detected_set:
                print(f"   Missing: {expected_set - detected_set}")
            if detected_set - expected_set:
                print(f"   Extra: {detected_set - expected_set}")
        
        # Show detailed results
        if detected_fallacies:
            print("   Details:")
            for fallacy in detected_fallacies:
                print(f"     - {fallacy.type}: {fallacy.explanation}")
                if fallacy.span:
                    print(f"       Span: \"{fallacy.span}\"")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Fallacy detection is working correctly.")
    else:
        print("⚠️  Some tests failed. Review the detection logic.")
    
    return passed_tests == total_tests


def demo_fallacy_severity():
    """Demonstrate fallacy severity classification"""
    
    print("\n🎯 Fallacy Severity Classification Demo")
    print("=" * 50)
    
    detector = FallacyDetector()
    
    severity_examples = [
        ("High Severity", "You're an idiot and your argument is stupid."),
        ("Medium Severity", "All politicians always lie to the public."),
        ("Low Severity", "Experts say that this is the best approach.")
    ]
    
    for severity_level, text in severity_examples:
        print(f"\n{severity_level}:")
        print(f"Text: \"{text}\"")
        
        fallacies = detector.detect(text)
        for fallacy in fallacies:
            severity = detector._get_fallacy_severity(fallacy.type)
            print(f"  - {fallacy.type} ({severity} severity): {fallacy.explanation}")


if __name__ == "__main__":
    print("🚀 FailSafe Advanced Fallacy Detection Test Suite")
    print("=" * 60)
    
    try:
        # Run main tests
        success = test_fallacy_detection()
        
        # Run severity demo
        demo_fallacy_severity()
        
        print(f"\n{'✅ SUCCESS' if success else '❌ FAILURE'}: Fallacy detection system is {'working' if success else 'needs improvement'}!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

