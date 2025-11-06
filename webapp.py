# ./webapp.py 

import argparse
import yaml
from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from flask_session import Session
from urllib.parse import urlparse
from factcheck.utils.config_loader import config
from tasks import celery_app, run_fact_check_task


app = Flask(__name__, static_folder="assets")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# --- Các bộ lọc Jinja không đổi ---
def zip_lists(a, b):
    return zip(a, b)


app.jinja_env.filters["zip"] = zip_lists


def count_occurrences(input_dict, target_string, key):
    if not isinstance(input_dict, list): 
        return 0
    input_list = [item.get(key) for item in input_dict]
    return input_list.count(target_string)


app.jinja_env.filters["count_occurrences"] = count_occurrences


def filter_evidences(input_dict, target_string, key):
    if not isinstance(input_dict, list): 
        return []
    return [item for item in input_dict if target_string == item.get(key)]


app.jinja_env.filters["filter_evidences"] = filter_evidences


def extract_hostname(url):
    """
    Một bộ lọc Jinja tùy chỉnh để trích xuất tên miền từ một URL.
    Ví dụ: 'https://www.example.com/page' -> 'example.com'
    """
    if not url or not isinstance(url, str):
        return ""
    try:
        # Sử dụng urlparse để phân tích URL
        hostname = urlparse(url).hostname
        # Loại bỏ 'www.' nếu có
        if hostname and hostname.startswith('www.'):
            return hostname[4:]
        return hostname or ""
    except Exception:
        return ""  # Trả về chuỗi rỗng nếu có lỗi

# Đăng ký bộ lọc mới với Jinja2


app.jinja_env.filters['url_host'] = extract_hostname


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        response_text = request.form.get("response", "")
        if not response_text.strip():
            return render_template("input.html", error="Please enter some text to check.")

        # THAY ĐỔI LỚN: Không gọi check_text() trực tiếp.
        # Thay vào đó, đẩy task vào hàng đợi Celery.
        # .delay() sẽ gửi task đi và trả về một đối tượng task ngay lập tức.
        task = run_fact_check_task.delay(response_text)
        
        # Chuyển hướng người dùng đến một trang loading,
        # truyền theo task_id để frontend có thể theo dõi.
        return redirect(url_for('loading_page', task_id=task.id))

    # Nếu là GET request, chỉ hiển thị trang nhập liệu
    return render_template("input.html")

# --- THAY ĐỔI 3: Thêm các Route mới để theo dõi và hiển thị kết quả ---


@app.route("/loading/<task_id>")
def loading_page(task_id):
    """
    Trang này chỉ hiển thị một spinner và có Javascript để kiểm tra trạng thái.
    """
    return render_template("loading.html", task_id=task_id)


@app.route('/status/<task_id>')
def task_status(task_id):
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {'state': task.state, 'status': 'Task is waiting in the queue...'}
    elif task.state == 'PROGRESS':  # Trạng thái tùy chỉnh của chúng ta
        response = {
            'state': task.state,
            'status': task.info.get('current_step', 'Processing...')
        }
    elif task.state == 'SUCCESS':
        task_result = task.get()
        session['factcheck_response'] = task_result.get('result')
        response = {'state': task.state, 'status': 'Complete!'}
    elif task.state != 'FAILURE':
        response = {'state': task.state, 'status': 'Starting up...'}
    else:  # FAILURE
        response = {
            'state': task.state,
            'status': 'An error occurred. Please try again.',
            'error': str(task.info)
        }
    return jsonify(response)


@app.route('/final_result')
def final_result_page():
    """
    Khi task hoàn thành, Javascript sẽ chuyển hướng đến đây.
    Hàm này lấy kết quả từ session và render trang kết quả cuối cùng.
    """
    response_data = session.get('factcheck_response', None)
    if response_data is None:
        # Xử lý trường hợp người dùng truy cập trực tiếp URL này
        return redirect(url_for('index'))
        
    # Sử dụng template final_result.html (tên cũ là FailSafe_fc.html)
    return render_template("final_result.html", responses=response_data, shown_claim=0)


# Route get_content để xem chi tiết từng claim vẫn giữ nguyên,
# vì nó đọc dữ liệu từ session.
@app.route("/shownClaim/<content_id>")
def get_content(content_id):
    response_data = session.get('factcheck_response', None)
    if response_data is None:
        return "Session expired or no data found. Please submit your text again.", 404
    try:
        claim_index = int(content_id) - 1
    except (ValueError, TypeError):
        return "Invalid claim ID.", 400
    num_claims = len(response_data.get('claim_detail', []))
    if not (0 <= claim_index < num_claims):
        claim_index = 0
    return render_template("final_result.html", responses=response_data, shown_claim=claim_index)


# --- THAY ĐỔI 2: Chạy app từ config ---
if __name__ == "__main__":
    app.run(
        host=config.get('webapp.host'),
        port=config.get('webapp.port'),
        debug=config.get('webapp.debug')
    )