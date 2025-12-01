# tasks.py 

import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from celery import Celery
from factcheck.utils.config_loader import config
from factcheck import build_fact_check_system

logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
logging.getLogger('chromadb').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.WARNING)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

project_dir = Path(__file__).resolve().parent

env_path = project_dir / '.env'

print(f"Attempting to load environment variables from: {env_path}")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print("Successfully loaded .env file.")

celery_app = Celery(
    'tasks',
    broker=config.get('celery.broker_url'),
    backend=config.get('celery.backend_url')
)

factcheck_instance = None


def get_factcheck_instance():
    global factcheck_instance
    if factcheck_instance is None:
        print("Celery Worker is initializing FactCheck instance for the first time...")
        
        factcheck_instance = build_fact_check_system(
            default_model=config.get('llm.default_model'),
            api_config=None,
            prompt_name=config.get('llm.default_prompt'),
            retriever_name=config.get('pipeline.retriever'),
        )
        print("FactCheck instance initialized for Celery Worker.")
    return factcheck_instance


@celery_app.task(bind=True)
def run_fact_check_task(self, text_to_check: str):
    instance = get_factcheck_instance()
    
    def update_progress(state, message, payload=None):

        meta = {
            'current_step': message,
            'data': payload or {} 
        }
        self.update_state(state=state, meta=meta)
        
        if payload and 'event' in payload:
            print(f"[PROGRESS] {message} (Event: {payload['event']})")
        else:
            print(f"[PROGRESS] {message}")
    try:
        update_progress('PROGRESS', 'Initializing pipeline...')
        
        result_data = instance.check_text_with_progress(text_to_check, update_progress)
        
        return {'status': 'SUCCESS', 'result': result_data}

    except Exception as e:
        print(f"!!! Task failed. Error: {e}")
        import traceback
        traceback.print_exc()
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise e 