# ./webapp.py

from flask import Flask, request, render_template, jsonify, session
from factcheck.utils.llmclient import CLIENTS
import argparse
import json
import yaml
from flask_session import Session 

from factcheck.utils.utils import load_yaml
from factcheck import FactCheck

app = Flask(__name__, static_folder="assets")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Define the custom filter
def zip_lists(a, b):
    return zip(a, b)


# Register the filter with the Jinja2 environment
app.jinja_env.filters["zip"] = zip_lists


# Occurrences count filter
def count_occurrences(input_dict, target_string, key):
    if not isinstance(input_dict, list):
        return 0
    input_list = [item.get(key) for item in input_dict]
    return input_list.count(target_string)


app.jinja_env.filters["count_occurrences"] = count_occurrences


# Filter evidences by relationship
def filter_evidences(input_dict, target_string, key):
    if not isinstance(input_dict, list):
        return []
    return [item for item in input_dict if target_string == item.get(key)]


app.jinja_env.filters["filter_evidences"] = filter_evidences


# --- CÁC ROUTE ĐÃ ĐƯỢC NÂNG CẤP ---

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        response_text = request.form.get("response", "")
        if not response_text.strip():
            # Nếu người dùng không nhập gì hoặc chỉ nhập khoảng trắng
            return render_template("input.html", error="Please enter some text to check.")

        # Gọi pipeline fact-checking
        response_data = factcheck_instance.check_text(response_text)

        # THAY ĐỔI QUAN TRỌNG: Lưu kết quả vào session thay vì file
        # Session sẽ lưu trữ dữ liệu riêng cho từng trình duyệt của người dùng
        session['factcheck_response'] = response_data

        # Trả về template với dữ liệu vừa nhận được
        return render_template("FailSafe_fc.html", responses=response_data, shown_claim=0)

    # Nếu là GET request, chỉ hiển thị trang nhập liệu
    return render_template("input.html")


@app.route("/shownClaim/<content_id>")
def get_content(content_id):
    # THAY ĐỔI QUAN TRỌNG: Lấy dữ liệu từ session của người dùng hiện tại
    response_data = session.get('factcheck_response', None)

    # Xử lý trường hợp không có dữ liệu trong session (ví dụ: session hết hạn,
    # người dùng truy cập trực tiếp URL này mà chưa submit gì)
    if response_data is None:
        return "Session expired or no data found. Please submit your text again.", 404

    try:
        # Đảm bảo content_id là một số nguyên hợp lệ
        claim_index = int(content_id) - 1
    except (ValueError, TypeError):
        # Nếu content_id không hợp lệ, trả về lỗi
        return "Invalid claim ID.", 400
    
    # Kiểm tra xem index có nằm trong phạm vi hợp lệ không
    num_claims = len(response_data.get('claim_detail', []))
    if not (0 <= claim_index < num_claims):
        claim_index = 0

    return render_template("FailSafe_fc.html", responses=response_data, shown_claim=claim_index)


# --- PHẦN KHỞI TẠO VÀ CẤU HÌNH GIỮ NGUYÊN ---

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, default="gemini-2.5-flash") 
parser.add_argument("--client", type=str, default="gemini", choices=CLIENTS.keys())
parser.add_argument("--prompt", type=str, default="gemini_prompt")
parser.add_argument("--retriever", type=str, default="hybrid")
parser.add_argument("--modal", type=str, default="text")
parser.add_argument("--input", type=str, default="demo_data/text.txt")
parser.add_argument("--api_config", type=str, default="factcheck/config/api_config.yaml")
args = parser.parse_args()

# Load API config from yaml file
try:
    api_config = load_yaml(args.api_config)
except FileNotFoundError as e:
    print(f"API config file not found: {e}")
    api_config = {}
except yaml.YAMLError as e:
    print(f"YAML error loading api config: {e}")
    api_config = {}

factcheck_instance = FactCheck(
    default_model=args.model,
    api_config=api_config,
    prompt=args.prompt,
    retriever=args.retriever,
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2024, debug=True)