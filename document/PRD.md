# PRD: n8n-research-assistant

**Project Name:** n8n-research-assistant
**Version:** 1.0
**Created:** 2025-10-19
**Owner:** [Your Name]
**Status:** Planning → Development

---

## 📋 1. 프로젝트 개요 (Executive Summary)

### 1.1 목적
학술 논문 리서치 과정을 자동화하여 **논문 검색 → 분석 → 정리** 워크플로우를 단축하고, 연구자가 논문 내용 이해와 작성에 집중할 수 있도록 지원

### 1.2 문제 정의
- ❌ Google Scholar에서 관련 논문 찾기 시간 소요 (30분~1시간)
- ❌ 논문 읽고 핵심 내용 정리하는 작업 반복 (논문당 2-3시간)
- ❌ IEEE 참고문헌 형식 맞추기 번거로움
- ❌ 코드가 있는 논문의 재현성 파악 어려움

### 1.3 솔루션
FastAPI 기반 백엔드 + n8n 워크플로우로 논문 검색부터 Notion 정리까지 자동화

### 1.4 핵심 가치
- ⏱️ **시간 절약**: 논문 5개 정리 시간 10시간 → 1시간으로 단축
- 🎯 **품질 향상**: AI 기반 일관된 요약 및 분석
- 📚 **체계적 관리**: Notion Database로 논문 데이터베이스 구축

---

## 🎯 2. 목표 및 범위 (Goals & Scope)

### 2.1 프로젝트 목표

#### Primary Goals (필수)
1. ✅ 키워드 기반 학술 논문 검색 (2024-2025년, IEEE/ACM 우선)
2. ✅ AI 기반 논문 요약 및 Contribution 추출
3. ✅ IEEE Citation 자동 생성
4. ✅ Notion Database 자동 저장

#### Secondary Goals (부가)
5. ⭐ GitHub 코드 분석 (README, 의존성)
6. ⭐ 논문 추천 시스템 (읽은 논문 기반)

#### Out of Scope (범위 외)
- ❌ 논문 PDF 전체 텍스트 파싱 (초록만 사용)
- ❌ 코드 실행/검증 (분석만)
- ❌ 논문 초안 자동 작성 (참고문헌만 제공)

### 2.2 타겟 사용자
- 석/박사 과정 연구자
- 산업 연구원
- 논문 작성이 필요한 개발자

---

## ⚙️ 3. 기술 스택 (Tech Stack)

### 3.1 Backend
- **Framework**: FastAPI (Python 3.10+)
- **API Client**: httpx, requests
- **Task Queue**: Celery (선택적, 나중에 추가)

### 3.2 External APIs
- **논문 검색**: Semantic Scholar API (무료)
- **논문 분석**: Claude API (Anthropic)
- **저장소**: Notion API
- **코드 분석**: GitHub API

### 3.3 Automation
- **n8n**: Workflow orchestration
- **Docker**: 컨테이너화 (FastAPI + n8n)

### 3.4 Database (선택적)
- **SQLite/PostgreSQL**: 검색 이력, 캐시

---

## 🔧 4. 기능 요구사항 (Functional Requirements)

### 4.1 Phase 1: 논문 검색 API (필수) ⭐

#### Feature 1.1: 키워드 검색
```
POST /api/v1/search/papers
```

**Request:**
```json
{
  "keyword": "transformer recommendation system",
  "year_from": 2024,
  "year_to": 2025,
  "limit": 20,
  "conferences": ["IEEE", "ACM", "NeurIPS", "CVPR"]
}
```

**Response:**
```json
{
  "query": "transformer recommendation system",
  "total_results": 18,
  "filtered_results": 5,
  "papers": [
    {
      "id": "semantic_scholar_id",
      "title": "Attention-based Collaborative Filtering...",
      "authors": ["Author A", "Author B"],
      "year": 2024,
      "venue": "IEEE TKDE",
      "citations": 15,
      "url": "https://...",
      "abstract": "...",
      "doi": "10.1109/...",
      "pdf_url": "https://..."
    }
  ]
}
```

**비즈니스 로직:**
1. Semantic Scholar API 호출
2. 연도 필터링 (2024-2025)
3. 컨퍼런스 필터링 (venue에 IEEE/ACM 포함)
4. Citation 수 기준 정렬
5. 상위 5개 반환

---

### 4.2 Phase 2: 논문 분석 API (필수) ⭐

#### Feature 2.1: 논문 요약 생성
```
POST /api/v1/analyze/summary
```

**Request:**
```json
{
  "paper_id": "semantic_scholar_id",
  "abstract": "This paper presents...",
  "include_contribution": true
}
```

**Response:**
```json
{
  "paper_id": "semantic_scholar_id",
  "summary": {
    "korean": "이 논문은 트랜스포머 기반 추천 시스템을...",
    "english": "This paper proposes a transformer-based..."
  },
  "contributions": [
    "새로운 attention mechanism 제안",
    "기존 대비 15% 성능 향상",
    "실시간 추천 가능한 경량화 모델"
  ],
  "key_findings": "...",
  "methodology": "..."
}
```

**사용 AI:**
- Claude API (Sonnet 4.5)

**Prompt Template:**
```python
SUMMARY_PROMPT = """
다음 논문 초록을 분석하여 아래 내용을 추출해주세요:

[초록]
{abstract}

[요구사항]
1. 핵심 내용 3줄 요약 (한글/영문)
2. 주요 기여도(Contribution) 3가지
3. 사용된 방법론
4. 주요 발견사항

형식: JSON
"""
```

---

#### Feature 2.2: IEEE Citation 생성
```
POST /api/v1/analyze/citation
```

**Request:**
```json
{
  "title": "Attention Is All You Need",
  "authors": ["A. Vaswani", "N. Shazeer"],
  "venue": "NeurIPS",
  "year": 2017,
  "pages": "5998-6008",
  "doi": "..."
}
```

**Response:**
```json
{
  "ieee_citation": "[1] A. Vaswani and N. Shazeer, \"Attention Is All You Need,\" in Proc. NeurIPS, Long Beach, CA, USA, 2017, pp. 5998-6008.",
  "bibtex": "@inproceedings{...}"
}
```

**로직:**
- Claude API로 IEEE Style 변환
- 또는 regex 기반 포맷팅

---

### 4.3 Phase 3: Notion 연동 (필수) ⭐

#### Feature 3.1: Notion Database 생성
```
POST /api/v1/notion/create-database
```

**Database 구조:**
| Property | Type | Description |
|----------|------|-------------|
| 제목 | Title | 논문 제목 |
| 저자 | Rich Text | 저자 목록 |
| 연도 | Number | 출판 연도 |
| 컨퍼런스 | Select | IEEE/ACM/기타 |
| 인용수 | Number | Citation count |
| 요약 | Rich Text | AI 생성 요약 |
| Contribution | Rich Text | 기여도 |
| IEEE Citation | Text | 참고문헌 |
| URL | URL | 논문 링크 |
| PDF | URL | PDF 링크 |
| GitHub | URL | 코드 링크 (선택) |
| Status | Select | 수집/분석/검증/완료 |
| 생성일 | Date | 자동 |

#### Feature 3.2: 논문 페이지 추가
```
POST /api/v1/notion/add-paper
```

**Request:**
```json
{
  "database_id": "notion_db_id",
  "paper": {
    "title": "...",
    "authors": "...",
    "summary": "...",
    "contribution": "...",
    "ieee_citation": "..."
  }
}
```

---

### 4.4 Phase 4: 코드 분석 (선택적) ⭐

#### Feature 4.1: GitHub 코드 분석
```
POST /api/v1/analyze/code
```

**Request:**
```json
{
  "github_url": "https://github.com/user/repo",
  "paper_title": "..."
}
```

**Response:**
```json
{
  "repository": "user/repo",
  "readme_summary": "이 코드는 PyTorch로 구현된...",
  "dependencies": {
    "python": "3.8+",
    "main_libraries": ["torch", "numpy", "transformers"]
  },
  "execution_guide": "1. pip install -r requirements.txt\n2. python train.py",
  "reproducibility_score": 0.8
}
```

**로직:**
1. GitHub API로 README.md 가져오기
2. requirements.txt, environment.yml 파싱
3. Claude API로 README 요약

---

## 🏗️ 5. API 아키텍처

### 5.1 디렉토리 구조
```
n8n-research-assistant/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 엔트리포인트
│   │   ├── config.py            # 환경변수 설정
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── search.py    # 논문 검색 엔드포인트
│   │   │   │   ├── analyze.py   # 논문 분석 엔드포인트
│   │   │   │   ├── notion.py    # Notion 연동 엔드포인트
│   │   │   │   └── code.py      # 코드 분석 엔드포인트
│   │   ├── services/
│   │   │   ├── semantic_scholar.py  # Semantic Scholar 클라이언트
│   │   │   ├── claude.py             # Claude API 클라이언트
│   │   │   ├── notion.py             # Notion API 클라이언트
│   │   │   └── github.py             # GitHub API 클라이언트
│   │   ├── models/
│   │   │   ├── paper.py         # 논문 데이터 모델
│   │   │   ├── analysis.py      # 분석 결과 모델
│   │   │   └── citation.py      # 참고문헌 모델
│   │   └── utils/
│   │       ├── prompts.py       # AI 프롬프트 템플릿
│   │       └── validators.py    # 입력 검증
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── n8n/
│   ├── workflows/
│   │   ├── 01-search-papers.json
│   │   ├── 02-analyze-papers.json
│   │   └── 03-notion-integration.json
│   └── docker-compose.yml
├── docs/
│   ├── API.md
│   └── SETUP.md
└── README.md
```

---

### 5.2 FastAPI 엔드포인트 전체 목록

```python
# 논문 검색
POST   /api/v1/search/papers              # 키워드 검색
GET    /api/v1/search/papers/{paper_id}   # 논문 상세 조회

# 논문 분석
POST   /api/v1/analyze/summary             # 요약 생성
POST   /api/v1/analyze/citation            # IEEE Citation 생성
POST   /api/v1/analyze/batch               # 여러 논문 일괄 분석

# Notion 연동
POST   /api/v1/notion/create-database      # Database 생성
POST   /api/v1/notion/add-paper            # 논문 추가
PUT    /api/v1/notion/update-paper/{id}    # 논문 업데이트

# 코드 분석 (선택)
POST   /api/v1/code/analyze                # GitHub 분석

# 유틸리티
GET    /api/v1/health                      # 헬스체크
GET    /api/v1/stats                       # 사용 통계
```

---

## 📊 6. 데이터 모델 (Data Models)

### 6.1 Paper Model
```python
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

class Paper(BaseModel):
    id: str
    title: str
    authors: List[str]
    year: int
    venue: str
    citations: int
    abstract: str
    url: HttpUrl
    pdf_url: Optional[HttpUrl] = None
    doi: Optional[str] = None
    github_url: Optional[HttpUrl] = None

class PaperAnalysis(BaseModel):
    paper_id: str
    summary_ko: str
    summary_en: str
    contributions: List[str]
    methodology: str
    key_findings: str
    ieee_citation: str
    created_at: datetime
```

---

## 🔐 7. 비기능 요구사항 (Non-Functional Requirements)

### 7.1 성능
- API 응답 시간: < 5초 (검색), < 30초 (분석)
- 동시 요청 처리: 10 requests/min
- 캐싱: 동일 키워드 24시간 캐시

### 7.2 보안
- API Key 환경변수 관리 (.env)
- Rate Limiting: 100 requests/hour per IP
- Input Validation: Pydantic 스키마

### 7.3 에러 처리
```python
{
  "error": {
    "code": "SEMANTIC_SCHOLAR_ERROR",
    "message": "Failed to fetch papers",
    "details": "..."
  }
}
```

### 7.4 로깅
- 모든 API 호출 로그
- 에러 스택 트레이스
- 사용량 통계 (논문 검색 횟수, API 비용)

---

## 📅 8. 개발 마일스톤

### Sprint 1 (1주): FastAPI 기본 구조 ⭐ **현재**
- [ ] FastAPI 프로젝트 초기화
- [ ] Semantic Scholar API 클라이언트 구현
- [ ] `/api/v1/search/papers` 엔드포인트 구현
- [ ] Docker 설정
- [ ] 테스트 코드 작성

**Deliverable:** 키워드 검색하면 논문 5개 반환

---

### Sprint 2 (1주): 논문 분석 기능
- [ ] Claude API 클라이언트 구현
- [ ] `/api/v1/analyze/summary` 엔드포인트
- [ ] `/api/v1/analyze/citation` 엔드포인트
- [ ] Prompt 엔지니어링 최적화

**Deliverable:** 초록 입력 → 요약 + IEEE Citation 출력

---

### Sprint 3 (1주): Notion 연동
- [ ] Notion API 클라이언트 구현
- [ ] Database 자동 생성 기능
- [ ] 논문 페이지 추가/업데이트 API
- [ ] n8n 워크플로우 설계

**Deliverable:** FastAPI → Notion 자동 저장

---

### Sprint 4 (선택, 1주): n8n 통합 & 코드 분석
- [ ] n8n 워크플로우 구현
- [ ] GitHub API 연동
- [ ] 코드 분석 기능
- [ ] 전체 통합 테스트

**Deliverable:** 키워드 입력 → 자동 Notion 정리 완성

---

## 📈 9. 성공 지표 (Success Metrics)

### 9.1 정량적 지표
- ✅ 논문 5개 검색 → 분석 → Notion 저장: **< 5분**
- ✅ AI 요약 정확도: 사용자 만족도 **> 80%**
- ✅ IEEE Citation 형식 정확도: **100%**
- ✅ API 가용성: **> 99%**

### 9.2 정성적 지표
- 논문 리서치 시간 50% 이상 단축
- 참고문헌 수동 작업 제거
- 체계적인 논문 데이터베이스 구축

---

## 🔄 10. n8n 워크플로우 설계

### Workflow 1: 자동 논문 검색 & 분석
```
[Manual Trigger: 키워드 입력]
    ↓
[HTTP Request: POST /api/v1/search/papers]
    ↓
[Loop: 각 논문]
    ↓
[HTTP Request: POST /api/v1/analyze/summary]
    ↓
[HTTP Request: POST /api/v1/analyze/citation]
    ↓
[HTTP Request: POST /api/v1/notion/add-paper]
    ↓
[Slack Notification: "5개 논문 분석 완료"]
```

---

## 🛠️ 11. 환경 설정 (Environment)

### .env 파일
```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-xxx
NOTION_API_KEY=secret_xxx
NOTION_DATABASE_ID=xxx

# Optional
GITHUB_TOKEN=ghp_xxx

# App Config
ENVIRONMENT=development
LOG_LEVEL=INFO
RATE_LIMIT=100
```

---

## ✅ 12. Definition of Done

각 기능이 완료되기 위한 조건:

- [ ] API 엔드포인트 구현 완료
- [ ] Unit Test 작성 (coverage > 80%)
- [ ] API 문서 작성 (FastAPI auto docs)
- [ ] 에러 핸들링 구현
- [ ] 로깅 추가
- [ ] Postman 테스트 통과
- [ ] README 업데이트

---

## 🚀 13. Quick Start (개발자용)

### 13.1 로컬 개발 환경 설정
```bash
# 1. Clone
git clone https://github.com/yourusername/n8n-research-assistant
cd n8n-research-assistant/backend

# 2. 가상환경
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 패키지 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일 편집

# 5. 실행
uvicorn app.main:app --reload

# 6. 테스트
curl http://localhost:8000/api/v1/health
```

---

## 📚 14. 참고 문서

- [Semantic Scholar API Docs](https://api.semanticscholar.org/)
- [Claude API Reference](https://docs.anthropic.com/claude/reference)
- [Notion API Guide](https://developers.notion.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [n8n Documentation](https://docs.n8n.io/)

---

## 🎯 15. Next Steps (지금 할 일)

### 👉 **Step 1: FastAPI 프로젝트 초기화**
```bash
mkdir -p n8n-research-assistant/backend
cd n8n-research-assistant/backend
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic httpx python-dotenv
```

### 👉 **Step 2: Semantic Scholar 검색 API 구현**
`app/services/semantic_scholar.py` 작성

### 👉 **Step 3: 첫 엔드포인트 테스트**
`POST /api/v1/search/papers`

---

