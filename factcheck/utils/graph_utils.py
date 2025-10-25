# ./factcheck/utils/graph_utils.py

import json
import os
from rdflib import Graph, Namespace, RDFS, URIRef
from rdflib.term import Literal, BNode

# === PHẦN SỬA ĐỔI QUAN TRỌNG: Xây dựng URI file đa nền tảng ===
from pathlib import Path
from urllib.request import pathname2url

# 1. Sử dụng pathlib để có đường dẫn đối tượng hóa, giúp code chạy đúng trên mọi HĐH
_current_file_path = Path(__file__).resolve()
# Đi từ file hiện tại -> thư mục utils -> thư mục factcheck -> thư mục gốc -> ontology/sag_ontology.jsonld
_ontology_path_obj = _current_file_path.parent.parent / "ontology" / "sag_ontology.jsonld"

# 2. Chuyển đổi đường dẫn Path object thành chuỗi
_ontology_path_str = str(_ontology_path_obj)

# 3. Sử dụng pathname2url để tạo URL path tương thích (quan trọng cho Windows)
#    Hàm này sẽ tự động xử lý ký tự đặc biệt và dấu ':' trong đường dẫn C:\
_ontology_path_url = pathname2url(_ontology_path_str)

# 4. Tạo URI hoàn chỉnh bắt đầu bằng file:///
#    Lưu ý có 3 dấu gạch chéo: file:// (scheme) + / (bắt đầu đường dẫn tuyệt đối)
ONTOLOGY_URI = f"file:///{_ontology_path_url}"
# === KẾT THÚC PHẦN SỬA ĐỔI ===

# Định nghĩa namespace để sử dụng trong các truy vấn SPARQL
SAG = Namespace("https://failsafe.factcheck.ai/ontology#")


def sag_to_graph(sag_jsonld: dict) -> Graph:
    """
    Loads a JSON-LD SAG into an rdflib Graph object.
    It forces the parser to use a local ontology file to avoid network access.
    Returns an empty graph if input is invalid.
    """
    g = Graph()
    if not sag_jsonld or not isinstance(sag_jsonld, dict) or "@graph" not in sag_jsonld:
        return g
    try:
        # Tạo một bản sao của dữ liệu để tránh thay đổi đối tượng gốc
        data_to_parse = sag_jsonld.copy()
        
        # === SỬA LỖI TRIỆT ĐỂ ===
        # Ghi đè trường @context bằng URI file cục bộ đã được chuẩn hóa.
        # Điều này buộc rdflib phải đọc context từ file trên ổ đĩa của bạn
        # thay vì cố gắng truy cập một URL trên internet.
        data_to_parse["@context"] = ONTOLOGY_URI
        # === KẾT THÚC SỬA LỖI ===
        
        # Parse dữ liệu JSON đã được sửa đổi
        g.parse(data=json.dumps(data_to_parse), format='json-ld')
        
    except Exception as e:
        # In lỗi chi tiết hơn để dễ dàng gỡ rối trong tương lai
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
    # SPARQL query để lấy ID và label của tất cả các node có type là sag:Claim
    query = """
    SELECT ?id ?label
    WHERE {
        ?id a sag:Claim .
        ?id rdfs:label ?label .
    }
    """
    # Gắn các tiền tố (prefix) vào graph để query ngắn gọn hơn
    graph.bind("sag", SAG)
    graph.bind("rdfs", RDFS)

    results = graph.query(query)
    
    claims = []
    for row in results:
        # row.id là một BNode/URIRef, row.label là một Literal. Chuyển chúng thành chuỗi.
        claims.append({
            "id": str(row.id),
            "label": str(row.label)
        })
    return claims


def graph_to_networkx_dict(graph: Graph) -> dict:
    """
    Converts an rdflib graph back to a dictionary format similar to the old one,
    suitable for visualization with networkx or sending to frontend.
    """
    nodes = []
    edges = []
    
    # Sử dụng cache để tránh truy vấn thông tin của một node nhiều lần
    node_cache = {}

    def format_node_id(node):
        """Định dạng ID của node để tương thích với JSON-LD blank node."""
        if isinstance(node, BNode):
            # Nếu là Blank Node, thêm lại tiền tố '_:'
            return f"_:{str(node)}"
        else:
            # Nếu là URI, giữ nguyên
            return str(node)

    # Lặp qua tất cả các bộ ba (triple) trong đồ thị để tìm các node và cạnh
    
    # 1. Tìm tất cả các nodes (chủ thể có nhãn)
    for s, p, o in graph.triples((None, RDFS.label, None)):
        # SỬA LỖI: Sử dụng hàm format_node_id
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

    # 2. Tìm tất cả các cạnh
    relationship_properties = [SAG.supports, SAG.attacks, SAG.explains, SAG.relatedTo]
    for prop in relationship_properties:
        for s, p, o in graph.triples((None, prop, None)):
            edges.append({
                # SỬA LỖI: Sử dụng hàm format_node_id cho cả source và target
                "source": format_node_id(s),
                "target": format_node_id(o),
                "label": str(p).split('#')[-1]
            })
            
    return {"nodes": nodes, "edges": edges}