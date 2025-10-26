# 🎓 Research Assistant - 지식 상태 기반 논문 리서치 자동화 시스템

## 📋 시스템 개요

세계 최고 연구실의 리서치 워크플로우를 자동화한 시스템입니다.

### 핵심 컨셉

**문제**:
- 같은 논문을 반복 검색하여 시간 낭비
- 어떤 논문부터 읽어야 할지 모름
- Foundation(뿌리) 논문과 최신 논문의 구분 없음
- 논문 간 관계(Citation Network) 파악 어려움

**솔루션**:
- ✅ 지식 상태 추적 (Beginner → Experienced)
- ✅ Citation Network 자동 구축
- ✅ 논문 자동 분류 (Foundation/Core/Recent)
- ✅ 중복 제거 및 진도율 관리
- ✅ Research Gap 자동 분석

---

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────┐
│                   n8n Workflow                   │
│  (지식 상태 기반 자동화 워크플로우)               │
└───────────────┬─────────────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────────────┐
│              FastAPI Backend                     │
│                                                   │
│  ┌─────────────────┐  ┌────────────────────┐   │
│  │  Search API     │  │  Knowledge API      │   │
│  │  - 논문 검색    │  │  - 주제 관리        │   │
│  │  - Citation Net │  │  - 진도율 추적      │   │
│  └─────────────────┘  └────────────────────┘   │
│                                                   │
│  ┌─────────────────────────────────────────┐   │
│  │         Services                         │   │
│  │  - SemanticScholar (논문 검색)          │   │
│  │  - KnowledgeManager (JSON 저장소)       │   │
│  └─────────────────────────────────────────┘   │
└───────────────┬─────────────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────────────┐
│           data/research_knowledge.json           │
│         (주제별 지식 상태 & 논문 데이터)          │
└─────────────────────────────────────────────────┘
```

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 1. 저장소 클론
cd /Users/hotseller/devJun/myWorkspace/myn8n/n8n-research-assistant

# 2. 환경변수 설정 (.env 파일 생성)
cat > .env << EOF
# Semantic Scholar API (선택, 없으면 무료 버전)
SEMANTIC_SCHOLAR_API_KEY=your_key_here

# OpenAI API (n8n Agent용)
OPENAI_API_KEY=your_key_here

# 환경 설정
ENVIRONMENT=development
EOF

# 3. Docker 컨테이너 실행
docker-compose up -d

# 4. API 확인
curl http://localhost:8000/api/v1/health
```

### 2. n8n 워크플로우 임포트

1. http://localhost:5678 접속
2. **Workflows** → **Import from File**
3. `My workflow.json` 선택
4. OpenAI 자격증명 설정

### 3. 첫 실행

```javascript
// Input Parameters 노드에서 설정
{
  "topic_name": "GNN Recommendation System",
  "keyword": "gnn recommendation system",
  "knowledge_state": "beginner",  // 처음 시작
  "year_from": 2024,
  "year_to": 2025,
  "limit": 10
}
```

**Execute Workflow** 클릭!

---

## 📊 워크플로우 동작 방식

### Week 1: Beginner (처음 시작)

```
[입력] "GNN Recommendation System", beginner

1️⃣ 주제 생성
   → research_knowledge.json에 새 주제 추가

2️⃣ 논문 검색
   → Semantic Scholar에서 10개 검색
   → 인용수 높은 순으로 정렬

3️⃣ Citation Network 구축
   → Top 1 논문(Seed)의 References 20개
   → Top 1 논문을 인용한 Citations 20개
   → 총 41개 논문 (Seed + 20 + 20)

4️⃣ AI 분석 (Agent)
   ✓ 논문 분류:
     - Foundation: 3개 (Attention, GNN, GCN)
     - Core: 5개 (LightGCN 등)
     - Recent: 2개 (2024-2025)

   ✓ 각 논문 분석:
     - 한글 요약
     - 기여도 (Contribution)
     - 방법론
     - 한계점
     - 데이터셋

   ✓ Research Gap:
     - 미해결 문제: Cold-start, Scalability
     - 최근 트렌드: Contrastive Learning
     - 연구 방향: Meta-learning

5️⃣ JSON 저장
   → data/research_knowledge.json 업데이트
   → 읽기 순서: [Foundation → Core → Recent]

6️⃣ 리포트 생성
   → GNN_Recommendation_System_research_report.json
```

### Week 2: 진행 중

```
[입력] 동일 주제 재검색

1️⃣ 주제 확인
   → 이미 존재함 (생성 스킵)

2️⃣ 논문 검색
   → 10개 검색

3️⃣ 중복 제거 ⭐
   → 8개는 이미 있음 (스킵)
   → 2개만 새 논문 추가

4️⃣ 분석 & 저장
   → 새 논문 2개만 분석 (비용 절약!)

5️⃣ 진도율 업데이트
   → 3/5 Foundation 읽음 → 60%
```

### Week 5: Experienced (전문가 모드)

```
[입력] knowledge_state = "experienced"

1️⃣ 검색 범위 축소
   → Foundation/Core 스킵
   → Recent 논문만 검색

2️⃣ 차이점 분석
   → "기존 Core 논문 대비 무엇이 바뀌었나?"
   → Contrastive Learning 추가됨

3️⃣ 트렌드 업데이트
   → research_gap의 recent_trends 갱신
```

---

## 🔑 핵심 기능

### 1. Citation Network (핵심!)

```python
# Seed 논문 중심으로 네트워크 구축
Seed Paper (LightGCN, 2020)
  ├─ References (이 논문이 인용한 논문)
  │   ├─ GCN (2018)
  │   ├─ Neural CF (2017)
  │   └─ ... (20개)
  │
  └─ Citations (이 논문을 인용한 논문)
      ├─ ContrastGCN (2024)
      ├─ MixGCF (2023)
      └─ ... (20개)
```

**왜 중요한가?**
- 논문의 **뿌리**(Foundation)를 찾을 수 있음
- 논문의 **후속 연구**(Citations)를 추적 가능
- 연구의 **흐름**(Timeline)을 파악

### 2. 지식 상태 자동 전환

```python
Beginner (0-79%)
  → Foundation 3개 + Core 5개 + Recent 2개 모두 탐색
  → 읽기: Foundation부터

Intermediate (80-94%)
  → Foundation 스킵, Core + Recent 탐색
  → 읽기: Core부터

Experienced (95-100%)
  → Foundation/Core 스킵, Recent만 추적
  → 읽기: 최신 논문만
```

### 3. 중복 제거 & 캐싱

```json
// research_knowledge.json
{
  "topics": {
    "gnn_recommendation_system": {
      "foundation_papers": [...],  // 이미 저장됨
      "core_papers": [...],        // 이미 저장됨
      "recent_papers": [...]       // 이미 저장됨
    }
  }
}

// 다음 검색 시
→ 이미 있는 논문 ID는 스킵
→ 새 논문만 추가 & 분석
```

### 4. Research Gap 자동 분석

Agent가 자동으로 도출:

```json
{
  "research_gap": {
    "unsolved_problems": [
      "Cold-start 문제 완전 해결 방법 없음",
      "대규모 그래프 실시간 추천 어려움"
    ],
    "potential_directions": [
      "Meta-learning으로 cold-start 해결",
      "분산 학습으로 scalability 개선"
    ]
  }
}
```

---

## 📁 파일 구조

```
n8n-research-assistant/
├── app/                          # FastAPI 백엔드
│   ├── api/v1/
│   │   ├── search.py             # 논문 검색 API
│   │   └── knowledge.py          # 지식 상태 관리 API
│   ├── services/
│   │   ├── semantic_scholar.py   # Semantic Scholar 클라이언트
│   │   └── knowledge_manager.py  # JSON 저장소 관리
│   └── models/
│       └── paper.py              # 데이터 모델
│
├── data/
│   ├── research_knowledge.json        # 주제별 지식 상태 (자동 생성)
│   └── research_knowledge_sample.json # 샘플 데이터
│
├── My workflow.json              # n8n 워크플로우
├── WORKFLOW_GUIDE.md             # 사용 가이드
└── docker-compose.yml            # Docker 설정
```

---

## 🎯 API 엔드포인트

### 논문 검색

#### 키워드 검색
```bash
POST /api/v1/search/papers
{
  "keyword": "gnn recommendation system",
  "year_from": 2024,
  "year_to": 2025,
  "limit": 10
}
```

#### Citation Network 구축
```bash
POST /api/v1/search/citation-network
{
  "paper_id": "abc123",
  "max_references": 20,
  "max_citations": 20
}
```

### 지식 관리

#### 주제 생성
```bash
POST /api/v1/knowledge/topics
{
  "topic_name": "GNN Recommendation System",
  "knowledge_state": "beginner"
}
```

#### 주제 조회
```bash
GET /api/v1/knowledge/topics/{topic_name}
```

#### 논문 추가
```bash
POST /api/v1/knowledge/topics/papers
{
  "topic_name": "GNN Recommendation System",
  "papers": [...],
  "category": "foundation"  # foundation/core/recent
}
```

#### 논문 읽음 표시
```bash
POST /api/v1/knowledge/topics/mark-read
{
  "topic_name": "GNN Recommendation System",
  "paper_id": "abc123",
  "category": "foundation"
}
```

---

## 💡 사용 팁

### 1. 새 주제 시작할 때

```javascript
// beginner로 시작
{
  "knowledge_state": "beginner",
  "limit": 10  // 충분한 논문 수
}
```

### 2. 이미 아는 주제

```javascript
// experienced로 시작
{
  "knowledge_state": "experienced",
  "limit": 5  // 최신 논문만
}
```

### 3. 정기적으로 업데이트

```bash
# 매주 금요일 실행 (n8n 스케줄러)
→ 새 논문 자동 추적
→ 트렌드 업데이트
```

### 4. 읽은 논문 표시

```bash
# API 호출 또는 JSON 직접 수정
curl -X POST http://localhost:8000/api/v1/knowledge/topics/mark-read \
  -H "Content-Type: application/json" \
  -d '{
    "topic_name": "GNN Recommendation System",
    "paper_id": "abc123",
    "category": "foundation"
  }'
```

---

## 🔧 확장 가능성

### Phase 1 (현재)
- ✅ Citation Network
- ✅ 지식 상태 관리
- ✅ 자동 분류
- ✅ Research Gap 분석

### Phase 2 (다음 단계)
- [ ] **Notion 연동**: Database 자동 저장
- [ ] **Slack 알림**: 새 논문 발견 시
- [ ] **PDF 다운로드**: Open Access 자동 다운로드
- [ ] **GitHub 코드 분석**: 재현 가능성 평가

### Phase 3 (미래)
- [ ] **자동 스케줄링**: 매주 자동 검색
- [ ] **논문 추천**: 읽은 논문 기반 추천
- [ ] **요약 PDF 생성**: 주간 리포트
- [ ] **벤치마크 추적**: 성능 지표 자동 업데이트

---

## 📖 참고 문서

- [WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md) - 워크플로우 상세 가이드
- [PRD.md](./document/PRD.md) - 프로젝트 요구사항 문서
- [Semantic Scholar API](https://api.semanticscholar.org/)
- [n8n Documentation](https://docs.n8n.io/)

---

## 🎓 연구 철학

이 시스템의 핵심 철학:

1. **Context 중심**: 개별 논문이 아닌 연구 흐름 파악
2. **효율성**: 중복 작업 제거, 읽어야 할 논문만 선별
3. **자동화**: 반복 작업은 시스템이 처리
4. **Gap 도출**: 단순 요약이 아닌 미해결 문제 발견

---

**Happy Researching! 🚀**

