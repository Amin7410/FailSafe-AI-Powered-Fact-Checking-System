# tasks.py (PHIÊN BẢN SỬA LỖI ĐƯỜNG DẪN .ENV)

# === THAY ĐỔI: CHỈ ĐƯỜNG DẪN TƯỜNG MINH ===
from dotenv import load_dotenv
from pathlib import Path
from celery import Celery
from factcheck.utils.config_loader import config
from factcheck import FactCheck

# 1. Xác định đường dẫn đến thư mục gốc của dự án
#    Path(__file__) là file tasks.py hiện tại
#    .resolve() lấy đường dẫn tuyệt đối
#    .parent trỏ đến thư mục cha (thư mục gốc của dự án)
project_dir = Path(__file__).resolve().parent

# 2. Tạo đường dẫn đầy đủ đến file .env
env_path = project_dir / '.env'

# 3. Gọi load_dotenv với đường dẫn cụ thể
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
        
        factcheck_instance = FactCheck(
            default_model=config.get('llm.default_model'),
            api_config=None,
            prompt=config.get('llm.default_prompt'),
            retriever=config.get('pipeline.retriever'),
        )
        print("FactCheck instance initialized for Celery Worker.")
    return factcheck_instance


@celery_app.task(bind=True)
def run_fact_check_task(self, text_to_check: str):
    """
    Task này sẽ cập nhật trạng thái của nó để frontend có thể hiển thị tiến trình.
    """
    instance = get_factcheck_instance()
    
    def update_progress(state, message):
        """Hàm tiện ích để gửi cập nhật trạng thái."""
        meta = {'current_step': message}
        self.update_state(state=state, meta=meta)
        print(f"[PROGRESS] {message}")

    try:
        # Bắt đầu
        update_progress('PROGRESS', 'Initializing pipeline...')
        
        # Hàm check_text gốc
        result_data = instance.check_text_with_progress(text_to_check, update_progress)
        
        # Hoàn thành
        return {'status': 'SUCCESS', 'result': result_data}

    except Exception as e:
        print(f"!!! Task failed. Error: {e}")
        import traceback
        traceback.print_exc()
        # Gửi trạng thái thất bại
        self.update_state(state='FAILURE', meta={'error': str(e)})
        # Celery sẽ tự động xử lý việc này, nhưng update_state giúp gửi thông điệp rõ hơn
        raise e  # Ném lại lỗi để Celery biết task đã thất bại