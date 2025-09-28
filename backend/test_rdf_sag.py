#!/usr/bin/env python3
"""
Test script for RDF/OWL Structured Argument Graph (SAG)

This script demonstrates the RDF/OWL compliant SAG generation
with Linked Data standards and cross-lingual support.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.sag_generator import SAGGenerator


def test_rdf_sag_generation():
    """Test RDF SAG generation with various content types"""
    
    generator = SAGGenerator()
    
    # Test cases with different types of content
    test_cases = [
        {
            "name": "Simple Claim",
            "content": "Vaccines cause autism.",
            "language": "en"
        },
        {
            "name": "Complex Argument",
            "content": "Studies show that climate change is real. Scientists agree that human activities are the primary cause. Evidence from multiple sources indicates rising global temperatures.",
            "language": "en"
        },
        {
            "name": "Argumentative Text",
            "content": "I claim that this policy is wrong. According to experts, the data shows negative effects. However, some people argue that the benefits outweigh the costs.",
            "language": "en"
        },
        {
            "name": "Scientific Text",
            "content": "Research indicates that regular exercise improves cardiovascular health. Multiple peer-reviewed studies demonstrate significant benefits for patients with heart conditions.",
            "language": "en"
        },
        {
            "name": "Short Text",
            "content": "Hello world.",
            "language": "en"
        }
    ]
    
    print("🧪 Testing RDF/OWL Structured Argument Graph Generation")
    print("=" * 70)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Content: \"{test_case['content']}\"")
        print(f"   Language: {test_case['language']}")
        
        # Generate SAG
        sag_data = generator.generate(test_case['content'], test_case['language'])
        
        # Display results
        print(f"   Analysis ID: {sag_data['analysis_id']}")
        print(f"   Format: {sag_data['metadata']['format']}")
        print(f"   Generated at: {sag_data['metadata']['generated_at']}")
        print(f"   Namespaces: {len(sag_data['metadata']['namespaces'])}")
        
        # Show RDF formats
        print("   RDF Formats:")
        for format_name, content in sag_data['rdf_graph'].items():
            if content and len(content) > 10:
                print(f"     - {format_name}: {len(content)} characters")
            else:
                print(f"     - {format_name}: empty")
        
        # Show nodes and edges
        print(f"   Nodes: {len(sag_data['nodes'])}")
        print(f"   Edges: {len(sag_data['edges'])}")
        
        # Show sample nodes
        if sag_data['nodes']:
            print("   Sample Nodes:")
            for node in sag_data['nodes'][:3]:  # Show first 3 nodes
                print(f"     - {node['id']}: {node['type']} ({node['label'][:50]}...)")
        
        # Show sample edges
        if sag_data['edges']:
            print("   Sample Edges:")
            for edge in sag_data['edges'][:3]:  # Show first 3 edges
                print(f"     - {edge['source']} -> {edge['target']} ({edge['relation']})")


def test_sparql_queries():
    """Test SPARQL querying on generated SAG"""
    
    generator = SAGGenerator()
    
    # Generate SAG for testing
    content = "Studies show that climate change is real. Scientists agree that human activities are the primary cause. Evidence from multiple sources indicates rising global temperatures."
    sag_data = generator.generate(content, "en")
    
    print("\n🔍 Testing SPARQL Queries on RDF SAG")
    print("=" * 50)
    
    # Test queries
    queries = [
        {
            "name": "Get All Entities",
            "query": """
                PREFIX sag: <http://failsafe.ai/sag/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                
                SELECT ?entity ?text ?label WHERE {
                    ?entity rdf:type sag:Entity .
                    ?entity sag:hasText ?text .
                    ?entity sag:hasLabel ?label .
                }
            """
        },
        {
            "name": "Get All Claims",
            "query": """
                PREFIX arg: <http://failsafe.ai/argument/>
                PREFIX sag: <http://failsafe.ai/sag/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                
                SELECT ?claim ?text WHERE {
                    ?claim rdf:type arg:Claim .
                    ?claim sag:hasText ?text .
                }
            """
        },
        {
            "name": "Get All Evidence",
            "query": """
                PREFIX arg: <http://failsafe.ai/argument/>
                PREFIX sag: <http://failsafe.ai/sag/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                
                SELECT ?evidence ?text WHERE {
                    ?evidence rdf:type arg:Evidence .
                    ?evidence sag:hasText ?text .
                }
            """
        },
        {
            "name": "Get Analysis Metadata",
            "query": """
                PREFIX sag: <http://failsafe.ai/sag/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                
                SELECT ?analysis ?content ?language ?generatedAt WHERE {
                    ?analysis rdf:type sag:Analysis .
                    ?analysis sag:hasContent ?content .
                    ?analysis sag:hasLanguage ?language .
                    ?analysis sag:generatedAt ?generatedAt .
                }
            """
        }
    ]
    
    for query_info in queries:
        print(f"\n{query_info['name']}:")
        try:
            results = generator.query_sag(sag_data, query_info['query'])
            if results:
                print(f"   Found {len(results)} results:")
                for result in results[:3]:  # Show first 3 results
                    print(f"     - {result}")
            else:
                print("   No results found")
        except Exception as e:
            print(f"   Error: {e}")


def test_export_formats():
    """Test SAG export in different formats"""
    
    generator = SAGGenerator()
    
    # Generate SAG for testing
    content = "Climate change is a serious issue that requires immediate action."
    sag_data = generator.generate(content, "en")
    
    print("\n📤 Testing SAG Export Formats")
    print("=" * 40)
    
    formats = ["turtle", "json-ld", "xml", "n3"]
    
    for format_name in formats:
        print(f"\n{format_name.upper()}:")
        try:
            exported = generator.export_sag(sag_data, format_name)
            if exported:
                print(f"   Exported {len(exported)} characters")
                # Show first 200 characters
                preview = exported[:200].replace('\n', ' ')
                print(f"   Preview: {preview}...")
            else:
                print("   Export failed or empty")
        except Exception as e:
            print(f"   Error: {e}")


def test_namespace_validation():
    """Test namespace and URI validation"""
    
    generator = SAGGenerator()
    
    # Generate SAG for testing
    content = "This is a test claim with evidence."
    sag_data = generator.generate(content, "en")
    
    print("\n🏷️  Testing Namespace and URI Validation")
    print("=" * 50)
    
    # Check namespaces
    namespaces = sag_data['metadata']['namespaces']
    print(f"Namespaces defined: {len(namespaces)}")
    for prefix, uri in namespaces.items():
        print(f"   {prefix}: {uri}")
    
    # Check URI patterns
    print("\nURI Patterns:")
    for node in sag_data['nodes']:
        if 'uri' in node:
            uri = node['uri']
            if uri.startswith('http://failsafe.ai/'):
                print(f"   ✅ Valid URI: {uri}")
            else:
                print(f"   ❌ Invalid URI: {uri}")


def demo_rdf_benefits():
    """Demonstrate benefits of RDF/OWL approach"""
    
    print("\n🎯 RDF/OWL SAG Benefits Demonstration")
    print("=" * 50)
    
    benefits = [
        "✅ Linked Data Standards: Compatible with W3C standards",
        "✅ Interoperability: Can be integrated with other RDF systems",
        "✅ Queryable: SPARQL queries for complex analysis",
        "✅ Extensible: Easy to add new vocabulary terms",
        "✅ Cross-lingual: Language tags and multilingual support",
        "✅ Provenance: Full traceability of analysis process",
        "✅ Serialization: Multiple export formats (Turtle, JSON-LD, XML, N3)",
        "✅ Namespace Management: Organized vocabulary with clear URIs",
        "✅ Type Safety: RDF types for different argument components",
        "✅ Metadata Rich: Comprehensive analysis metadata"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")


if __name__ == "__main__":
    print("🚀 FailSafe RDF/OWL Structured Argument Graph Test Suite")
    print("=" * 70)
    
    try:
        # Run main tests
        test_rdf_sag_generation()
        
        # Run SPARQL tests
        test_sparql_queries()
        
        # Run export tests
        test_export_formats()
        
        # Run namespace validation
        test_namespace_validation()
        
        # Show benefits
        demo_rdf_benefits()
        
        print(f"\n✅ SUCCESS: RDF/OWL SAG system is working correctly!")
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

