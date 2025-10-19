# 🔬 n8n Research Assistant

학술 논문 검색 및 분석 자동화 시스템

## 🚀 Features

- ✅ **논문 검색 API**: Semantic Scholar 공식 API 기반 빠른 검색
- ✅ **n8n 워크플로우**: 논문 검색부터 분석까지 자동화
- ✅ **환경변수 관리**: API Key 안전 관리
- ✅ **Docker 지원**: 간편한 배포

---

## 📦 Tech Stack

- **Backend**: FastAPI (Python 3.12)
- **Automation**: n8n
- **API**: Semantic Scholar, Claude (예정), Notion (예정)
- **Package Manager**: uv
- **Logging**: loguru

---

## 🛠️ Setup

### 1. Requirements

- Python 3.12+
- uv (Python 패키지 매니저)
- Docker & Docker Compose (선택)

### 2. Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd n8n-research-assistant

# 2. Install dependencies
uv sync

# 3. Setup API Key
cp .env.example .env
nano .env  # SEMANTIC_SCHOLAR_API_KEY 입력
```

**API Key 발급**: [docs/SETUP_API_KEY.md](docs/SETUP_API_KEY.md) 참고

### 3. Run

#### 로컬 실행
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Docker 실행
```bash
docker-compose up -d
```

---

## 📚 API Endpoints

### 🔍 논문 검색
```bash
POST /api/v1/search/papers
```

**Request:**
```json
{
  "keyword": "transformer recommendation system",
  "year_from": 2023,
  "year_to": 2025,
  "limit": 5
}
```

**Response:**
```json
{
  "query": "transformer recommendation system",
  "year_range": "2023-2025",
  "total_results": 5,
  "papers": [
    {
      "id": "xxx",
      "title": "...",
      "authors": ["..."],
      "year": 2024,
      "venue": "IEEE",
      "citations": 10,
      "url": "https://...",
      "abstract": "...",
      "doi": "...",
      "pdf_url": "https://..."
    }
  ]
}
```

### 📄 논문 상세 조회
```bash
GET /api/v1/search/papers/{paper_id}
```

### 🏥 헬스 체크
```bash
GET /api/v1/health
```

---

## 📖 API Documentation

서버 실행 후:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🐳 Docker Services

```bash
# 전체 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down
```

**Services:**
- `api`: FastAPI Backend (Port 8000)
- `n8n`: n8n Workflow Automation (Port 5678)

---

## 📁 Project Structure

```
n8n-research-assistant/
├── app/
│   ├── api/v1/          # API 엔드포인트
│   ├── services/        # 외부 API 클라이언트
│   ├── models/          # 데이터 모델
│   ├── utils/           # 유틸리티 (로거 등)
│   ├── config.py        # 환경 설정
│   └── main.py          # FastAPI 메인
├── docs/                # 문서
├── logs/                # 로그 파일
├── .env                 # 환경변수 (gitignore)
├── pyproject.toml       # 의존성
└── docker-compose.yml   # Docker 설정
```

---

## 🔐 Environment Variables

`.env` 파일:
```bash
# Semantic Scholar API (필수)
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here

# Anthropic Claude API (나중에)
ANTHROPIC_API_KEY=

# Notion API (나중에)
NOTION_API_KEY=
NOTION_DATABASE_ID=

# App Config
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## 🧪 Test

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Search papers
curl -X POST http://localhost:8000/api/v1/search/papers \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "machine learning",
    "year_from": 2023,
    "year_to": 2025,
    "limit": 3
  }'
```

---

## 📝 Development Roadmap

### ✅ Phase 1: 논문 검색 (완료)
- [x] Semantic Scholar API 통합
- [x] FastAPI 엔드포인트
- [x] Docker 설정

### 🚧 Phase 2: n8n 워크플로우 (진행 중)
- [ ] n8n 워크플로우 설계
- [ ] Claude API 통합 (논문 분석)
- [ ] Notion API 통합 (저장)

### 📅 Phase 3: 고급 기능
- [ ] 논문 추천 시스템
- [ ] GitHub 코드 분석
- [ ] 일괄 처리

---

## 📄 License

MIT License

---

## 🙏 Acknowledgments

- [Semantic Scholar API](https://www.semanticscholar.org/product/api)
- [n8n](https://n8n.io/)
- [FastAPI](https://fastapi.tiangolo.com/)
