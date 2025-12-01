# ./factcheck/utils/graph_utils.py

import json
import os
from rdflib import Graph, Namespace, RDFS, URIRef
from rdflib.term import Literal, BNode
from pathlib import Path
from urllib.request import pathname2url
from factcheck.utils.config_loader import PROJECT_ROOT

_current_file_path = Path(__file__).resolve()
_ontology_path_obj = PROJECT_ROOT / "factcheck" / "ontology" / "sag_ontology.jsonld"
_ontology_path_str = str(_ontology_path_obj)
_ontology_path_url = pathname2url(_ontology_path_str)

ONTOLOGY_URI = f"file:///{_ontology_path_url}"

SAG = Namespace("https://failsafe.factcheck.ai/ontology#")


def sag_to_graph(sag_jsonld: dict) -> Graph:
    g = Graph()
    if not sag_jsonld or not isinstance(sag_jsonld, dict) or "@graph" not in sag_jsonld:
        return g
    try:
        data_to_parse = sag_jsonld.copy()
     
        data_to_parse["@context"] = ONTOLOGY_URI
        g.parse(data=json.dumps(data_to_parse), format='json-ld')
        
    except Exception as e:
        import traceback
        print(f"Error parsing JSON-LD to graph: {e}")
        traceback.print_exc()
        return Graph() 
    return g


def get_claims_from_graph(graph: Graph) -> list[dict]:
    """
    Queries the graph to extract all nodes of type 'Claim'.
    Returns a list of dicts, each containing the node's id and label.
    """
    query = """
    SELECT ?id ?label
    WHERE {
        ?id a sag:Claim .
        ?id rdfs:label ?label .
    }
    """
    graph.bind("sag", SAG)
    graph.bind("rdfs", RDFS)

    results = graph.query(query)
    
    claims = []
    for row in results:
        claims.append({
            "id": str(row.id),
            "label": str(row.label)
        })
    return claims


def graph_to_networkx_dict(graph: Graph) -> dict:
    nodes = []
    edges = []
    node_cache = {}

    def format_node_id(node):
        if isinstance(node, BNode):
            return f"_:{str(node)}"
        else:
            return str(node)

    for s, p, o in graph.triples((None, RDFS.label, None)):
        node_id = format_node_id(s)
        
        if node_id not in node_cache:
            node_label = str(o)
            
            node_type = "Node"
            for _, _, nt in graph.triples((s, URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), None)):
                if '#' in str(nt):
                    node_type = str(nt).split('#')[-1]
                    break

            node_info = {"id": node_id, "label": node_label, "type": node_type}
            nodes.append(node_info)
            node_cache[node_id] = node_info
    relationship_properties = [SAG.supports, SAG.attacks, SAG.explains, SAG.relatedTo]
    for prop in relationship_properties:
        for s, p, o in graph.triples((None, prop, None)):
            edges.append({
                "source": format_node_id(s),
                "target": format_node_id(o),
                "label": str(p).split('#')[-1]
            })   
    return {"nodes": nodes, "edges": edges}