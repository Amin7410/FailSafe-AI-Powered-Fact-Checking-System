# ./webapp.py

import argparse
import yaml
import logging
from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from flask_session import Session
from urllib.parse import urlparse
from factcheck.utils.config_loader import config
from tasks import celery_app, run_fact_check_task

from factcheck.utils.web_util import is_url, scrape_url_content


app = Flask(__name__, static_folder="assets")

app.logger.setLevel(logging.DEBUG)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


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
    if not url or not isinstance(url, str): 
        return ""
    try:
        hostname = urlparse(url).hostname
        if hostname and hostname.startswith('www.'): 
            return hostname[4:]
        return hostname or ""
    except Exception: 
        return ""


app.jinja_env.filters['url_host'] = extract_hostname


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        app.logger.info("=" * 20 + " NEW REQUEST " + "=" * 20)
        app.logger.debug(f"Received form data: {request.form}")

        input_text = request.form.get("response", "")
        if not input_text.strip():
            app.logger.warning("Empty input. Re-rendering input page.")
            return render_template("input.html", error="Please enter some text or a URL to check.")

        text_to_check = input_text.strip()
        app.logger.info(f"Input sanitized: '{text_to_check}'")
        
        if is_url(text_to_check):
            app.logger.info("Input detected as URL. Starting URL processing.")
            content, error = scrape_url_content(text_to_check)
            
            if error:
                app.logger.error(f"Scraping failed. Error: '{error}'. Re-rendering input page.")
                return render_template("input.html", error=error)
            
            text_to_check = content 
            
            if not text_to_check or len(text_to_check) < 50:
                error_msg = f"Insufficient content extracted from URL (only {len(text_to_check)} chars). Need at least 50."
                app.logger.warning(error_msg)
                return render_template("input.html", error=error_msg)
            
            app.logger.info("URL scraped successfully with sufficient content.")
        else:
            app.logger.info("Input is standard text, not a URL.")

        app.logger.info("Preparing to send task to Celery...")
        task = run_fact_check_task.delay(text_to_check)
        app.logger.info(f"Task sent successfully! Task ID: {task.id}. Redirecting to loading page...")
        
        return redirect(url_for('loading_page', task_id=task.id))

    return render_template("input.html")


@app.route("/loading/<task_id>")
def loading_page(task_id):
    return render_template("loading.html", task_id=task_id)


@app.route('/status/<task_id>')
def task_status(task_id):
    """
    Check the status of the Celery task.
    Updated to return 'info' payload for Streaming Progress (Optimization #5).
    """
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {'state': task.state, 'status': 'Task is waiting in the queue...'}
    
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state, 
            'status': task.info.get('current_step', 'Processing...'),
            'info': task.info 
        }
        
    elif task.state == 'SUCCESS':
        task_result = task.get()
        session['factcheck_response'] = task_result.get('result')
        response = {'state': task.state, 'status': 'Complete!'}
        
    elif task.state != 'FAILURE':
        response = {'state': task.state, 'status': 'Starting up...'}
  
    else:
        response = {'state': task.state, 'status': 'An error occurred. Please try again.', 'error': str(task.info)}
        
    return jsonify(response)


@app.route('/final_result')
def final_result_page():
    response_data = session.get('factcheck_response', None)
    if response_data is None:
        return redirect(url_for('index'))
    return render_template("final_result.html", responses=response_data, shown_claim=0)


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


if __name__ == "__main__":
    app.run(
        host=config.get('webapp.host'),
        port=config.get('webapp.port'),
        debug=config.get('webapp.debug')
    )