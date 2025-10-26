# 연구원 논문 리서치 자동화 PRD (Product Requirements Document)

## 📌 프로젝트 개요

**목표**: 세계 최고 수준 연구실의 연구원처럼 논문을 체계적으로 조사하고 분석하는 완전 자동화 시스템 구축

**핵심 철학**:
- 연구원의 실제 사고 과정을 n8n 워크플로우로 시각화
- 지식 상태(초보 → 전문가)에 따라 검색 깊이 조절
- PDF를 끝까지 찾는 집요함 (5단계 폭포수 검색)
- 전문(Full-text) 기반 LLM 분석

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
현재 구현된 워크플로우:
1. Start Research
2. Input Parameters (키워드, 연도, 개수)
3. Search Papers
4. Split Papers (각 논문 개별 처리)
5. [1] Try Semantic Scholar
6. PDF Found? → True: Extract PDF Text
              → False: [2] Try arXiv
7. [2] Try arXiv → PDF Found? → True/False
8. [3] Try Unpaywall → PDF Found? → True/False
9. [4] Try Google Scholar → PDF Found? → True/False
10. [5] Try Google Search → PDF Found? → True/False
11. Give Up (No PDF)
12. Extract PDF Text
13. Basic LLM Chain (OpenAI)
14. Clean JSON (마크다운 제거)
15. Save Summary
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

### Phase 5: 지식 베이스 🚧 **진행 중**
- [x] 주제 생성/조회 API
- [x] 논문 추가 API
- [x] 논문 읽음 표시 API
- [ ] **n8n 워크플로우 통합** (다음 단계!)
- [ ] Foundation/Core/Recent 자동 분류
- [ ] 지식 상태 자동 업데이트

### Phase 6: Citation Network 📝 **대기 중**
- [x] Citation Network API (`POST /search/citation-network`)
- [ ] n8n 워크플로우 통합
- [ ] Backward/Forward Citation 분석
- [ ] 논문 분류 자동화

### Phase 7: Research Gap 분석 📝 **대기 중**
- [ ] 여러 논문 한계점 취합
- [ ] LLM Agent를 통한 연구 갭 탐지
- [ ] 연구 방향 제안
- [ ] 종합 보고서 생성

---

## 🎯 다음 단계 (Next Steps)

### 우선순위 1: 지식 베이스 통합 🔥
**목표**: 요약된 논문을 자동으로 주제별로 분류하고 저장

**구현 내용**:
1. `Save Summary` 이후 노드 추가:
   - `Create or Get Topic` (주제 생성/조회)
   - `Add Paper to Topic` (논문 추가)
   - `Classify Paper` (Foundation/Core/Recent 분류)
2. 분류 로직:
   - 논문 연도 기반 (예: 2020년 이전 → Foundation)
   - 인용수 기반 (예: 1000+ → Core)
   - 최신 논문 (예: 2024-2025 → Recent)

### 우선순위 2: Citation Network 통합
**목표**: Seed 논문의 참고문헌 및 인용 논문 자동 수집

**구현 내용**:
1. `Search Papers` 이후 Citation Network 노드 추가
2. Backward Citations → Foundation Papers
3. Forward Citations → Recent Papers
4. 각 논문에 대해 PDF 검색 및 요약 반복

### 우선순위 3: 지식 상태 기반 검색
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

