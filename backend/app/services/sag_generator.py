"""
Structured Argument Graph (SAG) Generator with RDF/OWL Support

Generates RDF/OWL compliant argument graphs from text content,
supporting Linked Data standards and cross-lingual knowledge representation.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Tuple
from datetime import datetime

import rdflib
from rdflib import Graph, Literal, Namespace, URIRef, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD
import spacy
from spacy import displacy

from .cache_service import cached

from ..models.report import FallacyItem
from ..core.config import get_settings


class SAGNamespace:
    """Namespace definitions for SAG RDF vocabulary"""
    
    def __init__(self):
        # Define custom namespaces
        self.SAG = Namespace("http://failsafe.ai/sag/")
        self.ARG = Namespace("http://failsafe.ai/argument/")
        self.CLAIM = Namespace("http://failsafe.ai/claim/")
        self.EVIDENCE = Namespace("http://failsafe.ai/evidence/")
        self.RELATION = Namespace("http://failsafe.ai/relation/")
        
        # Standard namespaces
        self.RDF = RDF
        self.RDFS = RDFS
        self.OWL = OWL
        self.XSD = XSD


class RDFSAGGenerator:
    """RDF-based Structured Argument Graph Generator"""
    
    def __init__(self):
        self.ns = SAGNamespace()
        self.nlp = self._load_spacy_model()
        self.graph = Graph()
        self._bind_namespaces()
    
    def _load_spacy_model(self):
        """Load spaCy model for NLP processing"""
        try:
            # Try to load English model
            return spacy.load("en_core_web_sm")
        except OSError:
            # Fallback to basic model
            try:
                return spacy.load("en_core_web_sm")
            except OSError:
                print("Warning: spaCy model not found. Install with: python -m spacy download en_core_web_sm")
                return None
    
    def _bind_namespaces(self):
        """Bind namespaces to the RDF graph"""
        self.graph.bind("sag", self.ns.SAG)
        self.graph.bind("arg", self.ns.ARG)
        self.graph.bind("claim", self.ns.CLAIM)
        self.graph.bind("evidence", self.ns.EVIDENCE)
        self.graph.bind("relation", self.ns.RELATION)
        self.graph.bind("rdf", self.ns.RDF)
        self.graph.bind("rdfs", self.ns.RDFS)
        self.graph.bind("owl", self.ns.OWL)
    
    @cached("sag_generation", ttl=1800)  # Cache for 30 minutes
    def generate(self, content: str, language: str = "en") -> Dict[str, Any]:
        """
        Generate RDF/OWL compliant Structured Argument Graph
        
        Args:
            content: Text content to analyze
            language: Language code (ISO 639-1)
            
        Returns:
            Dictionary containing RDF graph and metadata
        """
        if not content or len(content.strip()) < 10:
            return self._empty_sag()
        
        # Create new graph for this analysis
        self.graph = Graph()
        self._bind_namespaces()
        
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        analysis_uri = self.ns.SAG[f"analysis_{analysis_id}"]
        
        # Add analysis metadata
        self._add_analysis_metadata(analysis_uri, content, language)
        
        # Process content with spaCy
        if self.nlp:
            doc = self.nlp(content)
            self._process_spacy_doc(doc, analysis_uri)
        else:
            # Fallback processing without spaCy
            self._process_fallback(content, analysis_uri)
        
        # Extract argumentative structures
        self._extract_argumentative_structures(content, analysis_uri)
        
        # Serialize to different formats
        rdf_data = {
            "turtle": self.graph.serialize(format="turtle"),
            "json_ld": self.graph.serialize(format="json-ld"),
            "xml": self.graph.serialize(format="xml"),
            "n3": self.graph.serialize(format="n3")
        }
        
        # Extract nodes and edges for backward compatibility
        nodes, edges = self._extract_nodes_edges()
        
        return {
            "analysis_id": analysis_id,
            "language": language,
            "content": content,
            "rdf_graph": rdf_data,
            "nodes": nodes,
            "edges": edges,
            "raw": content,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "format": "rdf_owl_subset",
                "namespaces": {
                    "sag": str(self.ns.SAG),
                    "arg": str(self.ns.ARG),
                    "claim": str(self.ns.CLAIM),
                    "evidence": str(self.ns.EVIDENCE),
                    "relation": str(self.ns.RELATION)
                }
            }
        }
    
    def _add_analysis_metadata(self, analysis_uri: URIRef, content: str, language: str):
        """Add metadata about the analysis"""
        self.graph.add((analysis_uri, self.ns.RDF.type, self.ns.SAG.Analysis))
        self.graph.add((analysis_uri, self.ns.SAG.hasContent, Literal(content)))
        self.graph.add((analysis_uri, self.ns.SAG.hasLanguage, Literal(language, datatype=self.ns.XSD.language)))
        self.graph.add((analysis_uri, self.ns.SAG.generatedAt, Literal(datetime.utcnow().isoformat(), datatype=self.ns.XSD.dateTime)))
        self.graph.add((analysis_uri, self.ns.SAG.contentLength, Literal(len(content), datatype=self.ns.XSD.integer)))
    
    def _process_spacy_doc(self, doc, analysis_uri: URIRef):
        """Process spaCy document to extract linguistic structures"""
        # Extract entities
        for ent in doc.ents:
            entity_uri = self.ns.SAG[f"entity_{ent.start}_{ent.end}"]
            self.graph.add((entity_uri, self.ns.RDF.type, self.ns.SAG.Entity))
            self.graph.add((entity_uri, self.ns.SAG.hasText, Literal(ent.text)))
            self.graph.add((entity_uri, self.ns.SAG.hasLabel, Literal(ent.label_)))
            self.graph.add((entity_uri, self.ns.SAG.hasStart, Literal(ent.start, datatype=self.ns.XSD.integer)))
            self.graph.add((entity_uri, self.ns.SAG.hasEnd, Literal(ent.end, datatype=self.ns.XSD.integer)))
            self.graph.add((analysis_uri, self.ns.SAG.hasEntity, entity_uri))
        
        # Extract noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) > 1:  # Only multi-word phrases
                np_uri = self.ns.SAG[f"nounphrase_{chunk.start}_{chunk.end}"]
                self.graph.add((np_uri, self.ns.RDF.type, self.ns.SAG.NounPhrase))
                self.graph.add((np_uri, self.ns.SAG.hasText, Literal(chunk.text)))
                self.graph.add((np_uri, self.ns.SAG.hasStart, Literal(chunk.start, datatype=self.ns.XSD.integer)))
                self.graph.add((np_uri, self.ns.SAG.hasEnd, Literal(chunk.end, datatype=self.ns.XSD.integer)))
                self.graph.add((analysis_uri, self.ns.SAG.hasNounPhrase, np_uri))
        
        # Extract sentences and their relationships
        for sent in doc.sents:
            sent_uri = self.ns.SAG[f"sentence_{sent.start}_{sent.end}"]
            self.graph.add((sent_uri, self.ns.RDF.type, self.ns.SAG.Sentence))
            self.graph.add((sent_uri, self.ns.SAG.hasText, Literal(sent.text)))
            self.graph.add((sent_uri, self.ns.SAG.hasStart, Literal(sent.start, datatype=self.ns.XSD.integer)))
            self.graph.add((sent_uri, self.ns.SAG.hasEnd, Literal(sent.end, datatype=self.ns.XSD.integer)))
            self.graph.add((analysis_uri, self.ns.SAG.hasSentence, sent_uri))
    
    def _process_fallback(self, content: str, analysis_uri: URIRef):
        """Fallback processing without spaCy"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', content)
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                sent_uri = self.ns.SAG[f"sentence_{i}"]
                self.graph.add((sent_uri, self.ns.RDF.type, self.ns.SAG.Sentence))
                self.graph.add((sent_uri, self.ns.SAG.hasText, Literal(sentence.strip())))
                self.graph.add((analysis_uri, self.ns.SAG.hasSentence, sent_uri))
    
    def _extract_argumentative_structures(self, content: str, analysis_uri: URIRef):
        """Extract argumentative structures from content"""
        # Argumentative indicators
        claim_indicators = [
            r'\b(claim|assert|argue|maintain|contend|believe|think|say)\b',
            r'\b(it is|this is|that is)\s+(true|false|correct|wrong)\b',
            r'\b(evidence|proof|study|research)\s+(shows|proves|indicates|suggests)\b'
        ]
        
        evidence_indicators = [
            r'\b(according to|based on|studies show|research indicates)\b',
            r'\b(evidence|proof|data|statistics|findings)\b',
            r'\b(experts|scientists|doctors|professors)\s+(say|agree|believe)\b'
        ]
        
        # Extract claims
        for pattern in claim_indicators:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                claim_uri = self.ns.CLAIM[f"claim_{match.start()}_{match.end()}"]
                self.graph.add((claim_uri, self.ns.RDF.type, self.ns.ARG.Claim))
                self.graph.add((claim_uri, self.ns.SAG.hasText, Literal(match.group())))
                self.graph.add((claim_uri, self.ns.SAG.hasStart, Literal(match.start(), datatype=self.ns.XSD.integer)))
                self.graph.add((claim_uri, self.ns.SAG.hasEnd, Literal(match.end(), datatype=self.ns.XSD.integer)))
                self.graph.add((analysis_uri, self.ns.SAG.hasClaim, claim_uri))
        
        # Extract evidence
        for pattern in evidence_indicators:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                evidence_uri = self.ns.EVIDENCE[f"evidence_{match.start()}_{match.end()}"]
                self.graph.add((evidence_uri, self.ns.RDF.type, self.ns.ARG.Evidence))
                self.graph.add((evidence_uri, self.ns.SAG.hasText, Literal(match.group())))
                self.graph.add((evidence_uri, self.ns.SAG.hasStart, Literal(match.start(), datatype=self.ns.XSD.integer)))
                self.graph.add((evidence_uri, self.ns.SAG.hasEnd, Literal(match.end(), datatype=self.ns.XSD.integer)))
                self.graph.add((analysis_uri, self.ns.SAG.hasEvidence, evidence_uri))
    
    def _extract_nodes_edges(self) -> Tuple[List[Dict], List[Dict]]:
        """Extract nodes and edges for backward compatibility"""
        nodes = []
        edges = []
        
        # Extract nodes from RDF graph
        for subject, predicate, obj in self.graph:
            if isinstance(subject, URIRef):
                node_id = str(subject).split('/')[-1]
                if node_id not in [n['id'] for n in nodes]:
                    nodes.append({
                        "id": node_id,
                        "type": str(predicate) if predicate == self.ns.RDF.type else "unknown",
                        "label": str(obj) if isinstance(obj, Literal) else str(obj),
                        "uri": str(subject)
                    })
        
        # Extract edges from RDF graph
        for subject, predicate, obj in self.graph:
            if isinstance(subject, URIRef) and isinstance(obj, URIRef):
                source_id = str(subject).split('/')[-1]
                target_id = str(obj).split('/')[-1]
                edges.append({
                    "source": source_id,
                    "target": target_id,
                    "relation": str(predicate),
                    "type": "rdf_relation"
                })
        
        return nodes, edges
    
    def _empty_sag(self) -> Dict[str, Any]:
        """Return empty SAG structure"""
        return {
            "analysis_id": str(uuid.uuid4()),
            "language": "en",
            "content": "",
            "rdf_graph": {
                "turtle": "",
                "json_ld": "{}",
                "xml": "",
                "n3": ""
            },
            "nodes": [],
            "edges": [],
            "raw": "",
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "format": "rdf_owl_subset",
                "namespaces": {}
            }
        }


class SAGGenerator:
    """Main SAG Generator with RDF/OWL support"""
    
    def __init__(self):
        self.rdf_generator = RDFSAGGenerator()
    
    def generate(self, content: str, language: str = "en") -> dict:
        """
        Generate Structured Argument Graph with RDF/OWL support
        
        Args:
            content: Text content to analyze
            language: Language code (ISO 639-1)
            
        Returns:
            Dictionary containing RDF graph and backward-compatible structure
        """
        return self.rdf_generator.generate(content, language)
    
    def query_sag(self, sag_data: dict, sparql_query: str) -> List[Dict]:
        """
        Query SAG using SPARQL
        
        Args:
            sag_data: SAG data from generate()
            sparql_query: SPARQL query string
            
        Returns:
            List of query results
        """
        if "rdf_graph" not in sag_data:
            return []
        
        # Create temporary graph for querying
        temp_graph = Graph()
        temp_graph.parse(data=sag_data["rdf_graph"]["turtle"], format="turtle")
        
        # Execute SPARQL query
        results = temp_graph.query(sparql_query)
        
        # Convert results to list of dictionaries
        return [dict(row) for row in results]
    
    def export_sag(self, sag_data: dict, format: str = "turtle") -> str:
        """
        Export SAG in specified format
        
        Args:
            sag_data: SAG data from generate()
            format: Export format (turtle, json-ld, xml, n3)
            
        Returns:
            Serialized SAG data
        """
        if "rdf_graph" not in sag_data:
            return ""
        
        return sag_data["rdf_graph"].get(format, "")
    
    # def dict(self) -> Dict[str, Any]:
    #     """Convert SAG to dictionary for JSON serialization"""
    #     return {
    #         "analysis_id": getattr(self, 'analysis_id', None),
    #         "language": getattr(self, 'language', 'en'),
    #         "nodes": getattr(self, 'nodes', []),
    #         "edges": getattr(self, 'edges', []),
    #         "metadata": getattr(self, 'metadata', {}),
    #         "rdf_graph": getattr(self, 'rdf_graph', {})
    #     }



