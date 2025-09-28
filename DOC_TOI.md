# 🛡️ FailSafe - Hệ Thống AI Kiểm Chứng Sự Thật

FailSafe là hệ thống AI tiên tiến để kiểm chứng sự thật và phân tích tin giả, được thiết kế để giúp người dùng xác minh các tuyên bố và phát hiện lỗi logic trong thời gian thực.

## ✨ Tính Năng Chính

### 🔍 **Phân Tích Cốt Lõi**
- **Kiểm Chứng Sự Thật**: Xác minh toàn diện các tuyên bố bằng nhiều nguồn
- **Phát Hiện Lỗi Logic**: Phát hiện tiên tiến hơn 10 loại lỗi logic
- **Phát Hiện Nội Dung AI**: Phương pháp đa tín hiệu để nhận diện văn bản do AI tạo
- **Hỗ Trợ Đa Ngôn Ngữ**: Hỗ trợ hơn 10 ngôn ngữ với phát hiện tự động

### 🧠 **AI Nâng Cao**
- **Đồ Thị Lập Luận Có Cấu Trúc (SAG)**: Biểu diễn tri thức tuân thủ RDF/OWL
- **Chống Ảo Giác Nâng Cao**: Kiểm tra chéo đa tác nhân và tự phản ánh
- **Hiệu Chỉnh Độ Tin Cậy**: Chấm điểm tin cậy dựa trên TruthfulQA
- **Đồ Thị Tri Thức Đa Ngôn Ngữ**: Lập bản đồ khái niệm qua các ngôn ngữ

### ⚡ **Hiệu Suất & Giám Sát**
- **Bộ Nhớ Đệm Thông Minh**: Hệ thống bộ nhớ đệm đa tầng (bộ nhớ + đĩa)
- **Giám Sát Thời Gian Thực**: Chỉ số hiệu suất và kiểm tra sức khỏe
- **Gợi Ý Tối Ưu**: Khuyến nghị hiệu suất do AI hỗ trợ
- **Kiến Trúc Có Thể Mở Rộng**: Thiết kế cho thông lượng cao trong sản xuất

### 🔒 **Bảo Mật & Đạo Đức**
- **Giới Hạn Tốc Độ**: Giới hạn có thể cấu hình để ngăn chặn lạm dụng
- **Bảo Vệ Quyền Riêng Tư**: Xử lý dữ liệu tuân thủ GDPR
- **Phát Hiện Thiên Vị**: Phát hiện và giảm thiểu thiên vị tích hợp
- **Minh Bạch**: AI có thể giải thích với lý do chi tiết

## 🚀 Bắt Đầu Nhanh

### Yêu Cầu Hệ Thống
- Python 3.12+
- Node.js 18+
- Docker (tùy chọn)

### Cài Đặt Phát Triển

#### Tùy Chọn 1: Sử Dụng Script Phát Triển (Khuyến Nghị)

**Windows (PowerShell):**
```powershell
# Thiết lập môi trường phát triển
.\scripts\dev.ps1 setup

# Chạy backend
.\scripts\dev.ps1 backend

# Chạy frontend (trong terminal khác)
.\scripts\dev.ps1 frontend

# Chạy tests
.\scripts\dev.ps1 test

# Chạy với Docker
.\scripts\dev.ps1 docker
```

**Linux/macOS (Bash):**
```bash
# Thiết lập môi trường phát triển
./scripts/dev.sh setup

# Chạy backend
./scripts/dev.sh backend

# Chạy frontend (trong terminal khác)
./scripts/dev.sh frontend

# Chạy tests
./scripts/dev.sh test

# Chạy với Docker
./scripts/dev.sh docker
```

#### Tùy Chọn 2: Cài Đặt Thủ Công

**Backend:**
```bash
cd backend
pip install -r requirements.txt
# hoặc
poetry install
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Chạy với Docker

```bash
# Chạy tất cả services
docker-compose up --build

# Chạy trong background
docker-compose up -d --build
```

## 📖 Hướng Dẫn Sử Dụng

### Giao Diện Web

1. **Truy Cập**: Mở `http://localhost:5173`
2. **Nhập Tuyên Bố**: Nhập văn bản hoặc URL cần kiểm chứng
3. **Phân Tích**: Click "Analyze" để bắt đầu phân tích
4. **Xem Kết Quả**: Xem báo cáo chi tiết với:
   - Verdict (Kết luận): True/False/Mixed/Unverifiable
   - Confidence (Độ tin cậy): 0-100%
   - Evidence (Bằng chứng): Các nguồn hỗ trợ
   - Fallacies (Lỗi logic): Các lỗi được phát hiện
   - AI Detection: Phát hiện nội dung AI
   - SAG: Đồ thị lập luận có cấu trúc

### Browser Extension

1. **Cài Đặt**:
   - Mở Chrome: `chrome://extensions/`
   - Bật "Developer mode"
   - Click "Load unpacked"
   - Chọn folder: `frontend/extension`

2. **Sử Dụng**:
   - Chọn văn bản trên bất kỳ trang web nào
   - Right-click → "Fact Check with FailSafe"
   - Hoặc click icon extension → "Analyze Page"

### API Usage

**Phân tích văn bản:**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "Vaccines cause autism"}'
```

**Phân tích URL:**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

## 🏗️ Kiến Trúc Hệ Thống

### Backend (FastAPI)
- **API Layer**: RESTful endpoints
- **Service Layer**: Business logic
- **Data Layer**: Database models
- **AI Layer**: ML models và processing

### Frontend (React + TypeScript)
- **Web Interface**: Giao diện người dùng chính
- **Browser Extension**: Chrome extension
- **Components**: Reusable UI components

### Database
- **SQLite**: Development (mặc định)
- **PostgreSQL**: Production
- **Redis**: Caching và session storage

## 🧪 Testing

### Chạy Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

### Adversarial Testing
```bash
# Chạy adversarial tests
curl -X POST "http://localhost:8000/api/v1/testing/run_suite" \
  -H "Content-Type: application/json" \
  -d '{"test_types": ["noise_injection", "semantic_perturbation"]}'
```

## 📊 Monitoring

### Health Checks
```bash
# Kiểm tra sức khỏe hệ thống
curl http://localhost:8000/api/v1/health/liveness
curl http://localhost:8000/api/v1/health/readiness
```

### Metrics Dashboard
- Truy cập: `http://localhost:8000/api/v1/monitor/metrics_dashboard`
- Xem: CPU, Memory, Disk, Network usage
- Alerts: Cảnh báo tự động

### Logs
```bash
# Xem logs
tail -f logs/failsafe.log

# Clear logs
curl -X DELETE http://localhost:8000/api/v1/monitor/logs
```

## 🌍 Hỗ Trợ Đa Ngôn Ngữ

### Ngôn Ngữ Được Hỗ Trợ
- **Đầy đủ**: English, Spanish, French, German
- **Cơ bản**: Chinese, Arabic, Japanese, Korean
- **Tự động phát hiện**: Ngôn ngữ được phát hiện tự động

### Cấu Hình Ngôn Ngữ
```yaml
# ethical_config.yaml
multilingual:
  enabled: true
  default_language: "auto"
  supported_languages: ["en", "es", "fr", "de", "zh", "ar"]
  translation_service: "google"  # hoặc "azure", "aws"
```

## ⚙️ Cấu Hình

### Cấu Hình Chính
File: `backend/app/core/ethical_config.yaml`

```yaml
# Giới hạn tốc độ
rate_limit:
  requests_per_minute: 60
  burst_limit: 10

# Logging
logging:
  level: "INFO"
  format: "json"
  file: "logs/failsafe.log"

# Verification
verification:
  confidence_threshold: 0.7
  max_sources: 10
  timeout_seconds: 30

# Cache
cache:
  enabled: true
  ttl_seconds: 3600
  max_size_mb: 100
```

### Biến Môi Trường
```bash
# Database
export DATABASE_URL="postgresql://user:pass@localhost/failsafe"

# Redis
export REDIS_URL="redis://localhost:6379"

# API Keys
export OPENAI_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"

# Logging
export LOG_LEVEL="INFO"
```

## 🚀 Triển Khai Production

### Docker Deployment
```bash
# Build và chạy
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale failsafe-backend=3
```

### Cloud Deployment
- **AWS**: ECS, Lambda, RDS
- **Google Cloud**: Cloud Run, Cloud SQL
- **Azure**: Container Instances, Database

### Monitoring Production
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards
- **ELK Stack**: Log aggregation

## 🔧 Troubleshooting

### Lỗi Thường Gặp

**1. Backend không khởi động:**
```bash
# Kiểm tra dependencies
cd backend
pip list

# Kiểm tra logs
tail -f logs/failsafe.log
```

**2. Frontend không load:**
```bash
# Kiểm tra Node.js version
node --version  # Cần >= 18

# Clear cache
npm cache clean --force
rm -rf node_modules
npm install
```

**3. Database connection error:**
```bash
# Kiểm tra database
sqlite3 failsafe.db ".tables"

# Reset database
rm failsafe.db
python -c "from app.db.session import create_tables; create_tables()"
```

**4. Extension không hoạt động:**
- Kiểm tra manifest.json
- Reload extension trong Chrome
- Kiểm tra console errors

### Debug Mode
```bash
# Backend debug
export DEBUG=true
uvicorn app.main:app --reload --log-level debug

# Frontend debug
npm run dev -- --debug
```

## 📞 Hỗ Trợ

### Tài Liệu
- **API Reference**: `docs/API_REFERENCE.md`
- **Development Guide**: `docs/DEVELOPMENT_GUIDE.md`
- **User Manual**: `docs/USER_MANUAL.md`
- **Deployment Guide**: `docs/DEPLOYMENT_GUIDE.md`

### Liên Hệ
- **GitHub Issues**: Báo cáo bugs và yêu cầu tính năng
- **Discord**: Hỗ trợ real-time từ cộng đồng
- **Email**: minhdinhkhoi@gmail.com

## 🤝 Đóng Góp

### Cách Đóng Góp
1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

### Code Style
- **Backend**: Black, isort, flake8
- **Frontend**: Prettier, ESLint
- **Commits**: Conventional Commits

## 📄 License

MIT License - Xem file `LICENSE` để biết thêm chi tiết.

## 🙏 Acknowledgments

- **OpenAI**: GPT models
- **Hugging Face**: Transformers library
- **FastAPI**: Web framework
- **React**: Frontend framework
- **Community**: Contributors và testers

---

**FailSafe** - Bảo vệ thông tin, xây dựng niềm tin! 🛡️






