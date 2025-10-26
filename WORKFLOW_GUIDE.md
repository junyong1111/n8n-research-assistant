# 🚀 Research Assistant Workflow Guide

## 개요

이 워크플로우는 **지식 상태 기반 논문 리서치 자동화 시스템**입니다.

### 핵심 기능
- ✅ 지식 상태 추적 (Beginner → Experienced)
- ✅ Citation Network 자동 구축 (References + Citations)
- ✅ AI 기반 논문 분류 (Foundation/Core/Recent)
- ✅ Research Gap 자동 분석
- ✅ 읽기 순서 자동 생성
- ✅ 중복 논문 자동 필터링

---

## 워크플로우 구조

```
[Start]
  ↓
[Input Parameters] - 주제, 키워드, 지식 상태 입력
  ↓
[Check Topic Exists] - 주제가 이미 존재하는지 확인
  ↓
[Topic Exists?] - 분기
  ├─ NO → [Create New Topic] - 새 주제 생성
  └─ YES → [Search Papers] - 바로 검색
        ↓
[Build Citation Network] - Seed 논문의 References + Citations 가져오기
  ↓
[Research Analysis Agent] - AI가 논문 분류 & 분석
  ↓
[Save Papers] - Foundation/Core/Recent로 분류 저장
  ↓
[Generate Report] - JSON 리포트 생성
```

---

## 사용 방법

### 1. 입력 파라미터 설정

워크플로우를 실행하기 전 `Input Parameters` 노드에서 다음을 설정하세요:

```javascript
{
  "topic_name": "GNN Recommendation System",  // 연구 주제
  "keyword": "gnn recommendation system",     // 검색 키워드
  "knowledge_state": "beginner",              // beginner/intermediate/experienced
  "year_from": 2024,                          // 검색 시작 연도
  "year_to": 2025,                            // 검색 종료 연도
  "limit": 10                                 // 검색할 논문 수
}
```

### 2. 지식 상태 (Knowledge State)

#### Beginner (초심자)
- **동작**: 뿌리 논문(Foundation)부터 최신 논문까지 전부 탐색
- **읽기 순서**: Foundation → Core → Recent
- **예시**: 새로운 주제를 처음 시작할 때

#### Intermediate (중급자)
- **동작**: Core 논문부터 탐색
- **읽기 순서**: Core → Recent
- **예시**: 기초는 알고 있을 때

#### Experienced (숙련자)
- **동작**: Recent 논문만 탐색 (최신 트렌드 추적)
- **읽기 순서**: Recent only
- **예시**: 이미 주제를 잘 알고 있을 때

### 3. 자동 상태 전환

시스템이 자동으로 지식 상태를 업데이트합니다:

- **진행률 80% 달성** → Beginner → Intermediate
- **진행률 95% 달성** → Intermediate → Experienced

---

## API 엔드포인트

### 논문 검색
```bash
POST http://api:8000/api/v1/search/papers
{
  "keyword": "gnn recommendation system",
  "year_from": 2024,
  "year_to": 2025,
  "limit": 10
}
```

### Citation Network 구축
```bash
POST http://api:8000/api/v1/search/citation-network
{
  "paper_id": "abc123",
  "include_references": true,
  "include_citations": true,
  "max_references": 20,
  "max_citations": 20
}
```

### 주제 생성
```bash
POST http://api:8000/api/v1/knowledge/topics
{
  "topic_name": "GNN Recommendation System",
  "knowledge_state": "beginner"
}
```

### 주제 조회
```bash
GET http://api:8000/api/v1/knowledge/topics/GNN%20Recommendation%20System
```

### 논문 추가
```bash
POST http://api:8000/api/v1/knowledge/topics/papers
{
  "topic_name": "GNN Recommendation System",
  "papers": [...],
  "category": "foundation"  // foundation/core/recent
}
```

### 논문 읽음 표시
```bash
POST http://api:8000/api/v1/knowledge/topics/mark-read
{
  "topic_name": "GNN Recommendation System",
  "paper_id": "abc123",
  "category": "foundation"
}
```

---

## Agent 프롬프트

Research Analysis Agent는 다음 작업을 수행합니다:

1. **논문 분류**
   - Foundation: 뿌리 논문 (예: Attention, GCN)
   - Core: 핵심 방법론 (예: LightGCN)
   - Recent: 최신 연구 (2024-2025)

2. **논문별 분석**
   - 한글 요약 (3문장)
   - 주요 기여도 (3개)
   - 방법론
   - 한계점
   - 사용 데이터셋

3. **Research Gap 분석**
   - 공통 문제점
   - 미해결 문제
   - 최근 트렌드
   - 잠재적 연구 방향

4. **읽기 순서 제안**
   - Knowledge state에 따라 최적 순서 제시

---

## 출력 결과

### JSON 리포트 예시

```json
{
  "categorized_papers": {
    "foundation": [
      {
        "id": "attention2017",
        "title": "Attention Is All You Need",
        "year": 2017,
        "reason": "Self-attention 메커니즘의 기초"
      }
    ],
    "core": [
      {
        "id": "lightgcn2020",
        "title": "LightGCN",
        "year": 2020,
        "reason": "GCN 추천 시스템의 핵심 방법론"
      }
    ],
    "recent": [...]
  },
  "paper_analyses": [...],
  "research_gap": {
    "unsolved_problems": [
      "Cold-start 문제 완전 해결 방법 없음",
      "대규모 그래프 실시간 추천 어려움"
    ],
    "potential_directions": [
      "Meta-learning으로 cold-start 해결",
      "경량화 + 분산 학습"
    ]
  },
  "reading_order": ["attention2017", "gcn2018", "lightgcn2020", ...]
}
```

---

## 데이터 저장 위치

### JSON 파일
```
data/research_knowledge.json
```

### 리포트 파일
```
GNN_Recommendation_System_research_report.json
```

---

## 사용 시나리오

### Week 1: 새 주제 시작 (Beginner)
```
1. topic_name: "GNN Recommendation System"
2. knowledge_state: "beginner"
3. 실행 → 10개 논문 + Citation Network (41개)
4. AI 분석 → Foundation 3개, Core 5개, Recent 2개
5. 추천 읽기 순서: Foundation부터 시작
```

### Week 2: 기초 완료 (Intermediate)
```
1. 동일 주제로 재실행
2. 시스템이 자동으로 중복 제거 → 새 논문 2개만 추가
3. 읽은 논문 표시 → 진행률 80% → Intermediate로 전환
```

### Week 5: 전문가 모드 (Experienced)
```
1. knowledge_state: "experienced"
2. 실행 → Recent 논문만 추적
3. 기존 Core 논문과 비교 분석
```

---

## 트러블슈팅

### API 연결 실패
```bash
# Docker 컨테이너 확인
docker ps

# API 헬스 체크
curl http://localhost:8000/api/v1/health
```

### OpenAI API 에러
- n8n의 OpenAI 자격증명 확인
- API 키가 유효한지 확인

### Citation Network 에러
- Seed 논문 ID가 올바른지 확인
- Semantic Scholar API Rate Limit (무료: 100 req/5min)

---

## 다음 단계

1. **Notion 연동**: 분석 결과를 Notion Database에 자동 저장
2. **Slack 알림**: 새 논문 발견 시 알림
3. **GitHub 코드 분석**: 논문의 재현 가능성 자동 평가
4. **PDF 다운로드**: Open Access 논문 자동 다운로드

---

## 문의

이슈가 있으면 GitHub Issues에 등록해주세요!

