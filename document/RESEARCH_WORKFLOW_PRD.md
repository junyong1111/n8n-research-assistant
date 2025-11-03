# 연구원 논문 리서치 자동화 PRD (Product Requirements Document)

## 📌 프로젝트 개요

**목표**: 세계 최고 수준 연구실의 연구원처럼 논문을 체계적으로 조사하고 분석하는 완전 자동화 시스템 구축

**핵심 철학**:
- **Top-Tier 연구원 워크플로우 구현**: Seed 논문 → Citation Network → Research Gap 분석
- 연구원의 실제 사고 과정을 n8n 워크플로우로 시각화
- PDF를 끝까지 찾는 집요함 (5단계 폭포수 검색)
- 전문(Full-text) 기반 LLM 분석
- **Research Gap 자동 탐지**: 한계점 취합 → 트렌드 분석 → 연구 방향 제안

---

## 🎯 Main Workflow (Top-Tier Researcher)

```
[입력] keyword: "GNN recommendation system"
  ↓
[Step 1] Seed 논문 찾기
  → 인용수 Top 1 논문 (예: LightGCN)
  ↓
[Step 2] Citation Network 구축
  → References: Seed가 인용한 논문 20개
  → Citations: Seed를 인용한 논문 20개
  → 총 41개 논문 (Seed + 20 + 20)
  ↓
[Step 3] 중복 제거 & 캐시 비교
  → papers_cache.json과 비교
  → 새 논문만 필터링
  ↓
[Step 4] 논문별 심층 분석 (LLM Agent)
  각 논문:
  - 요약
  - 문제 정의
  - 제안 방법
  - 한계점 ⭐ (Research Gap 핵심!)
  - 사용 데이터셋
  - 성능
  ↓
[Step 5] Research Gap 분석 (LLM Agent)
  전체 논문을 보고:
  - 현재 연구의 주요 트렌드는?
  - 대부분의 논문이 공통적으로 해결 못한 문제는?
  - 2024-2025년 새로운 접근법은?
  - 내가 기여할 수 있는 부분은?
  ↓
[Step 6] 구조화된 리포트 생성
  research_report.json:
  {
    "topic": "GNN Recommendation System",
    "seed_paper": {...},
    "citation_tree": [...],
    "trends": {
      "2020-2022": "GCN 기반 경량화",
      "2023-2025": "Contrastive Learning + GNN"
    },
    "research_gaps": [
      "Cold-start 문제 여전히 미해결",
      "설명가능성(Explainability) 부족",
      "대규모 그래프 scalability 이슈"
    ],
    "recommended_papers_to_read": [top 5],
    "potential_research_directions": [...]
  }
```

---

## 🎯 핵심 기능 요구사항

### 1. 지식 상태 기반 논문 검색 (Knowledge-Based Search)

#### 1.1 지식 상태 관리
- [ ] **초보자 모드**: 기초 논문(뿌리) → 핵심 논문 → 최신 논문 순서로 검색
- [ ] **중급자 모드**: 핵심 논문 → 최신 논문
- [ ] **전문가 모드**: 최신 SOTA 논문만 검색
- [ ] 주제별 지식 상태 저장 (`data/research_knowledge.json`)
- [ ] 논문 읽음 표시 및 진행도 추적

#### 1.2 논문 분류 체계
- [ ] **Foundation Papers**: 해당 분야의 기초가 되는 논문 (예: Transformer, Attention)
- [ ] **Core Papers**: 핵심 방법론 논문 (예: BERT, GPT)
- [ ] **Recent Papers**: 최신 SOTA 논문 (최근 1-2년)

#### 1.3 Citation Network 분석
- [ ] Seed 논문 선정 (인용수 기반)
- [ ] Backward Citations (참고문헌) 분석 → Foundation Papers
- [ ] Forward Citations (인용된 논문) 분석 → Recent Papers
- [ ] Citation 깊이 조절 (지식 상태 기반)

---

### 2. 다단계 PDF 검색 시스템 (Multi-Source PDF Discovery)

#### 2.1 5단계 폭포수 검색 ✅ **완료**
- [x] **[1단계] Semantic Scholar**: 로컬 캐시 → API PDF URL
- [x] **[2단계] arXiv**: arXiv ID 기반 PDF 다운로드
- [x] **[3단계] Unpaywall**: DOI 기반 Open Access PDF
- [x] **[4단계] Google Scholar**: 제목+저자 검색
- [x] **[5단계] Google Search**: 제목 + "filetype:pdf" 검색
- [x] 각 단계마다 실패 시 다음 단계로 자동 이동
- [x] 모든 단계 실패 시 "Give Up" 처리

#### 2.2 PDF 검증 및 관리 ✅ **완료**
- [x] 로컬 PDF 파일 크기 검증 (최소 1KB)
- [x] PDF 텍스트 추출 가능 여부 확인
- [x] 손상된 파일 자동 삭제 및 재다운로드
- [x] PDF 캐시 관리 (`data/papers_pdf/`)

#### 2.3 n8n 워크플로우 시각화 ✅ **완료**
- [x] 각 PDF 검색 단계를 개별 HTTP Request 노드로 구현
- [x] If 노드로 성공/실패 분기 처리
- [x] 에러 아이템 필터링 (`pdf_found && !detail`)

---

### 3. LLM 기반 논문 분석 (AI-Powered Analysis)

#### 3.1 전문(Full-text) 추출 ✅ **완료**
- [x] PDF → 텍스트 추출 (`pdfplumber` + `PyPDF2`)
- [x] 첫 20,000자 추출 (LLM 컨텍스트 제한)
- [x] 메타데이터 추출 (페이지 수, 저자 등)

#### 3.2 LLM 요약 생성 ✅ **완료**
- [x] **Basic LLM Chain** 노드 사용 (OpenAI GPT-4o-mini)
- [x] 한국어 요약 생성 (`summary_ko`)
- [x] 핵심 기여도 추출 (`key_contributions`)
- [x] 방법론, 결과, 한계점, 데이터셋 정리
- [x] JSON 형식 강제 출력

#### 3.3 마크다운 제거 및 저장 ✅ **완료**
- [x] **Clean JSON** Code 노드로 ` ```json ` 제거
- [x] 요약 저장 API (`POST /papers/summary`)
- [x] 저장 위치: `data/paper_summaries/{paper_id}.json`

---

### 4. Research Gap 분석 (미구현)

#### 4.1 자동 연구 갭 탐지
- [ ] 여러 논문의 한계점(limitations) 취합
- [ ] 공통 트렌드 및 미해결 문제 식별
- [ ] LLM Agent를 통한 연구 방향 제안

#### 4.2 보고서 생성
- [ ] 주제별 종합 보고서 자동 생성
- [ ] Foundation → Core → Recent 흐름 시각화
- [ ] 연구 갭 및 제안 사항 정리

---

### 5. 지식 베이스 관리 (Knowledge Base)

#### 5.1 주제별 논문 관리 (부분 완료)
- [x] 주제 생성 API (`POST /knowledge/topics`)
- [x] 논문 추가 API (`POST /knowledge/topics/papers`)
- [x] 논문 읽음 표시 (`POST /knowledge/topics/papers/mark-read`)
- [ ] 주제별 논문 분류 자동화 (Foundation/Core/Recent)
- [ ] 지식 상태 자동 업데이트

#### 5.2 데이터 영속성
- [x] JSON 파일 기반 저장 (`data/research_knowledge.json`)
- [x] PDF 캐시 (`data/papers_cache.json`)
- [x] 요약 저장 (`data/paper_summaries/`)
- [ ] 데이터베이스 마이그레이션 (향후)

---

## 🏗️ 시스템 아키텍처

### Backend (FastAPI)
```
app/
├── api/v1/
│   ├── search.py          ✅ 논문 검색, Citation Network
│   ├── knowledge.py       ✅ 지식 베이스 관리
│   └── papers.py          ✅ PDF 검색 (5단계), 텍스트 추출, 요약 저장
├── services/
│   ├── semantic_scholar.py  ✅ Semantic Scholar API
│   └── pdf_processor.py     ✅ PDF 다운로드, 텍스트 추출, 다중 소스 검색
└── models/
    └── paper.py           ✅ 데이터 모델
```

### Workflow (n8n)
```
현재 구현된 워크플로우 (Top-Tier Researcher):
1. Start Research
2. Input Parameters (키워드, 연도, 개수)
3. Search Papers
4. Get Seed Paper (Top 1) ⭐ NEW!
5. Build Citation Network (Seed + 20 References + 20 Citations) ⭐ NEW!
6. Flatten Citation Network (41개 논문) ⭐ NEW!
7. Split Papers (각 논문 개별 처리)
8. [1] Try Semantic Scholar
9. PDF Found? → True: Extract PDF Text
              → False: [2] Try arXiv
10. [2] Try arXiv → PDF Found? → True/False
11. [3] Try Unpaywall → PDF Found? → True/False
12. [4] Try Google Scholar → PDF Found? → True/False
13. [5] Try Google Search → PDF Found? → True/False
14. Give Up (No PDF)
15. Extract PDF Text
16. Enhanced LLM Analysis (문제/방법/한계점/데이터셋/성능/향후연구) ⭐ ENHANCED!
17. Clean JSON (마크다운 제거)
18. Save Summary
19. Create or Get Topic (주제 생성/조회)
20. Classify & Add to Topic (자동 분류 및 저장)
21. Wait for All Papers (모든 논문 처리 대기)
22. Analyze Research Gaps (트렌드/한계점/연구갭/연구방향) ⭐ NEW!
23. Clean Gap JSON
24. Generate Report (마크다운 보고서 생성)
```

---

## ✅ 현재 진행 상황 체크리스트

### Phase 1: 기본 인프라 ✅ **완료**
- [x] FastAPI 프로젝트 구조 설정
- [x] Docker Compose 환경 구성
- [x] Semantic Scholar API 연동
- [x] 로깅 시스템 구축

### Phase 2: PDF 검색 시스템 ✅ **완료**
- [x] 5단계 폭포수 검색 API 구현
- [x] 각 단계별 개별 엔드포인트 분리
  - [x] `/papers/{id}/try-semantic-scholar`
  - [x] `/papers/{id}/try-arxiv`
  - [x] `/papers/{id}/try-unpaywall`
  - [x] `/papers/{id}/try-google-scholar`
  - [x] `/papers/{id}/try-google-search`
- [x] PDF 검증 로직 (파일 크기, 텍스트 추출 가능 여부)
- [x] 손상된 파일 자동 삭제 및 재시도

### Phase 3: n8n 워크플로우 ✅ **완료**
- [x] 5단계 PDF 검색 노드 구현
- [x] If 노드로 성공/실패 분기
- [x] 에러 아이템 필터링 (`pdf_found && !detail`)
- [x] Extract PDF Text 노드
- [x] Basic LLM Chain 노드 (OpenAI)
- [x] Clean JSON 노드 (마크다운 제거)
- [x] Save Summary 노드

### Phase 4: LLM 분석 ✅ **완료**
- [x] PDF 텍스트 추출 (`/papers/{id}/pdf-text`)
- [x] OpenAI GPT-4o-mini 연동
- [x] 한국어 요약 생성
- [x] JSON 형식 강제 및 마크다운 제거
- [x] 요약 저장 API (`POST /papers/summary`)

### Phase 5: 지식 베이스 ✅ **완료**
- [x] 주제 생성/조회 API
- [x] 논문 추가 API
- [x] 논문 읽음 표시 API
- [x] **n8n 워크플로우 통합** ✅
- [x] Foundation/Core/Recent 자동 분류 ✅
- [x] 지식 상태 자동 업데이트 ✅

### Phase 6: Citation Network 📝 **대기 중**
- [x] Citation Network API (`POST /search/citation-network`)
- [ ] n8n 워크플로우 통합
- [ ] Backward/Forward Citation 분석
- [ ] 논문 분류 자동화

### Phase 6: 보고서 생성 ✅ **완료**
- [x] 마크다운 보고서 생성 서비스 (`ReportGenerator`)
- [x] 주제별 보고서 조회 API (`GET /knowledge/topics/{topic_name}/report`)
- [x] n8n 워크플로우에 보고서 생성 노드 추가 (`Wait for All Papers` + `Generate Report`)
- [x] `reports/` 디렉토리 자동 생성

### Phase 7: Top-Tier Researcher Workflow ✅ **완료!**
**목표**: Seed 논문 기반 Citation Network → Research Gap 분석 → 구조화된 리포트

#### 7.1 Seed 논문 선정 ✅
- [x] 키워드 검색 후 인용수 Top 1 선정 (Code 노드)
- [x] Seed 논문 상세 정보 저장

#### 7.2 Citation Network 구축 ✅
- [x] Citation Network API (`POST /search/citation-network`)
- [x] n8n 워크플로우 통합 (`Build Citation Network` 노드)
- [x] References (Seed가 인용한 논문) 20개 수집
- [x] Citations (Seed를 인용한 논문) 20개 수집
- [x] Flatten 로직 (Seed + References + Citations)

#### 7.3 논문별 심층 분석 (Enhanced) ✅
- [x] LLM Agent 프롬프트 강화 (`Enhanced LLM Analysis`):
  - 문제 정의 (Problem Statement)
  - 제안 방법 (Proposed Method)
  - **한계점 (Limitations)** ⭐
  - 사용 데이터셋 (Datasets)
  - 성능 지표 (Performance Metrics)
  - 향후 연구 (Future Work)

#### 7.4 Research Gap 분석 (LLM Agent) ✅
- [x] 전체 논문 한계점 취합 (`Analyze Research Gaps` 노드)
- [x] 시간대별 트렌드 분석 (2020-2022, 2023-2025)
- [x] 공통 미해결 문제 식별
- [x] 연구 방향 제안

#### 7.5 구조화된 리포트 생성 ✅
- [x] Research Gap JSON 생성:
  - `topic`: 주제명
  - `total_papers_analyzed`: 분석 논문 수
  - `trends`: 시간대별 트렌드
  - `common_limitations`: 공통 한계점
  - `research_gaps`: 미해결 문제 목록
  - `recommended_papers_to_read`: Top 5 추천
  - `potential_research_directions`: 연구 방향 제안
- [x] 마크다운 보고서 생성 (기존 `Generate Report` 활용)

---

## 🎯 다음 단계 (Next Steps)

### 우선순위 1: Top-Tier Researcher Workflow 구현 🔥 **최우선!**
**목표**: Seed 논문 → Citation Network → Research Gap 분석 → 구조화된 리포트

**구현 계획**:
1. **Seed 논문 선정 로직**
   - `Search Papers` 결과에서 인용수 Top 1 선택
   - n8n: `Sort` 노드 + `Limit` 노드

2. **Citation Network 통합**
   - n8n: `Build Citation Network` 노드 추가
   - API: 기존 `POST /search/citation-network` 활용
   - References 20개 + Citations 20개 수집

3. **중복 제거 & 캐시 비교**
   - n8n: `Filter New Papers` 노드
   - `papers_cache.json`과 비교하여 새 논문만 처리

4. **LLM 프롬프트 강화**
   - 기존 요약 → **심층 분석**으로 변경
   - 문제 정의, 제안 방법, **한계점**, 데이터셋, 성능 추가

5. **Research Gap 분석 Agent**
   - 새 노드: `Analyze Research Gaps`
   - 전체 논문의 한계점을 LLM에 입력
   - 트렌드, 미해결 문제, 연구 방향 도출

6. **구조화된 JSON 리포트**
   - `research_report.json` 생성
   - 마크다운 보고서에 Research Gap 섹션 추가

**예상 워크플로우**:
```
Search Papers → Sort by Citations → Get Top 1 (Seed)
  ↓
Build Citation Network (41 papers)
  ↓
Filter New Papers (캐시 비교)
  ↓
Split Papers → PDF 검색 (5단계) → Extract Text
  ↓
Enhanced LLM Analysis (문제/방법/한계점/데이터셋/성능)
  ↓
Save to Knowledge Base
  ↓
Wait for All Papers
  ↓
Analyze Research Gaps (LLM Agent)
  ↓
Generate Structured Report (JSON + Markdown)
```

---

### ~~우선순위 1: 지식 베이스 통합~~ ✅ **완료!**
**목표**: 요약된 논문을 자동으로 주제별로 분류하고 저장

**구현 완료**:
1. ✅ `Save Summary` 이후 노드 추가:
   - ✅ `Create or Get Topic` (주제 생성/조회)
   - ✅ `Classify & Add to Topic` (자동 분류 및 추가)
2. ✅ 분류 로직:
   - 최신 논문 (2023-2025) → **Recent**
   - 기초 논문 (10년 이상 + 인용수 500+) → **Foundation**
   - 핵심 논문 (5년 이상 + 인용수 100+) → **Foundation**
   - 그 외 → **Core**
3. ✅ API 엔드포인트: `POST /api/v1/knowledge/classify-and-add`

### ~~우선순위 2: 보고서 생성 시스템~~ ✅ **완료!**
**목표**: 수집된 논문을 읽기 쉬운 마크다운 보고서로 자동 생성

**구현 완료**:
1. ✅ `ReportGenerator` 서비스 클래스 생성
   - ✅ `research_knowledge.json` 파싱
   - ✅ `paper_summaries/` 통합
   - ✅ 마크다운 템플릿 적용
2. ✅ API 엔드포인트: `GET /knowledge/topics/{topic_name}/report`
3. ✅ n8n 노드: `Wait for All Papers` + `Generate Report`
4. ✅ 보고서 저장: `reports/{topic_name}_{timestamp}.md` + `{topic_name}_latest.md`

**보고서 구조**:
- 📊 요약 (논문 수, 카테고리별 분포, 지식 상태)
- 🏛️ Foundation Papers (기초 논문)
- 🔬 Core Papers (핵심 논문)
- 🚀 Recent Papers (최신 논문)
- 📝 각 논문의 LLM 요약 포함 (한국어 요약, 핵심 기여, 방법론, 결과, 한계점, 데이터셋)
- 📝 메타데이터 (생성일, 도구, 데이터 소스)

### 우선순위 3: Citation Network 통합
**목표**: Seed 논문의 참고문헌 및 인용 논문 자동 수집

**구현 내용**:
1. `Search Papers` 이후 Citation Network 노드 추가
2. Backward Citations → Foundation Papers
3. Forward Citations → Recent Papers
4. 각 논문에 대해 PDF 검색 및 요약 반복

### 우선순위 4: 지식 상태 기반 검색
**목표**: 사용자의 지식 수준에 따라 검색 깊이 조절

**구현 내용**:
1. 주제별 지식 상태 확인
2. 초보자: Foundation → Core → Recent 순서
3. 전문가: Recent만 검색
4. 읽은 논문 자동 스킵

---

## 📊 성공 지표 (Success Metrics)

### 기술 지표
- [x] PDF 발견율: 80% 이상 (5단계 검색)
- [x] PDF 텍스트 추출 성공률: 95% 이상
- [x] LLM 요약 생성 성공률: 100%
- [ ] 논문 분류 정확도: 90% 이상
- [ ] 전체 워크플로우 실행 시간: 논문당 < 2분

### 사용자 경험
- [x] n8n에서 각 단계 시각적 확인 가능
- [x] 에러 발생 시 자동 복구 (다음 소스 시도)
- [ ] 주제별 논문 자동 정리
- [ ] 연구 갭 자동 탐지 및 제안

---

## 🐛 알려진 이슈 및 제약사항

### 해결된 이슈 ✅
- [x] ~~PDF Found가 true인데 실제로는 없는 경우~~ → 파일 크기 검증 추가
- [x] ~~LLM 출력에 마크다운 포함~~ → Clean JSON 노드 추가
- [x] ~~에러 아이템이 True Branch로 전달~~ → If 조건에 `!detail` 추가
- [x] ~~OpenAI Credential 에러~~ → Basic LLM Chain + OpenAI Chat Model 사용

### 현재 제약사항
- ⚠️ Google Scholar/Search: 봇 차단 가능 (Rate Limit)
- ⚠️ Semantic Scholar: 5,000 req/5min (API Key 필요)
- ⚠️ LLM 컨텍스트: 20,000자 제한 (긴 논문은 일부만 분석)
- ⚠️ 이미지 기반 PDF: 텍스트 추출 불가 (OCR 미구현)

---

## 📚 참고 자료

### API 문서
- Semantic Scholar: https://api.semanticscholar.org
- Unpaywall: https://unpaywall.org/products/api
- OpenAI: https://platform.openai.com/docs

### 내부 문서
- `WORKFLOW_GUIDE.md`: n8n 워크플로우 사용 가이드
- `README_SYSTEM.md`: 시스템 아키텍처 및 설정
- `document/PRD.md`: 초기 PRD

---

## 🚀 향후 계획 (Future Roadmap)

### Short-term (1-2주)
- [ ] 지식 베이스 n8n 통합
- [ ] Citation Network n8n 통합
- [ ] 논문 자동 분류 (Foundation/Core/Recent)

### Mid-term (1개월)
- [ ] Research Gap 분석 LLM Agent
- [ ] 종합 보고서 자동 생성
- [ ] 웹 UI 구축 (논문 브라우징)

### Long-term (3개월+)
- [ ] PostgreSQL 마이그레이션
- [ ] 멀티 유저 지원
- [ ] 논문 추천 시스템
- [ ] 실시간 알림 (새 논문 발표 시)

---

**작성일**: 2025-10-26
**버전**: 1.0
**작성자**: AI Research Assistant
**상태**: Phase 4 완료, Phase 5 진행 중

