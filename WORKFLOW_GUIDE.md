# n8n 워크플로우 가이드 - 연구원 사고 방식

## 🧠 핵심 컨셉

이 워크플로우는 **실제 연구원이 논문을 찾는 과정**을 자동화합니다.

```
연구원의 실제 사고:
"논문 찾았다 → PDF 있나? → 없네 → arXiv 찾아보자 → 없네
→ DOI로 Unpaywall 시도 → 없네 → Google Scholar 검색해보자
→ 없네 → Google 검색으로 마지막 시도 → 있다! 다운로드!"
```

이 과정을 **n8n 노드로 시각화**하여 각 단계를 명확히 볼 수 있습니다!

---

## 📊 워크플로우 구조

### 1️⃣ 논문 검색 단계
```
Start Research
  ↓
Input Parameters (키워드, 연도, 개수)
  ↓
Search Papers (Semantic Scholar API)
  ↓
Split Papers (각 논문 개별 처리)
```

### 2️⃣ PDF 찾기 단계 (연구원 사고 방식!)

각 논문마다 **5단계 폭포수 검색**을 수행합니다:

```
[1] Try Semantic Scholar
  ↓ (PDF 없으면)
[2] Try arXiv
  ↓ (PDF 없으면)
[3] Try Unpaywall (DOI 기반)
  ↓ (PDF 없으면)
[4] Try Google Scholar
  ↓ (PDF 없으면)
[5] Try Google Search
  ↓ (PDF 없으면)
Give Up (No PDF) ❌
```

**각 단계마다 If 노드**로 성공 여부를 확인하고, 실패하면 다음 소스를 시도합니다!

### 3️⃣ 분석 단계 (PDF 찾았을 때만)

```
Extract PDF Text
  ↓
Call OpenAI (GPT-4o-mini)
  ↓
Save Summary
```

---

## 🔧 API 엔드포인트 (개별 단계)

각 PDF 검색 단계는 **독립적인 API 엔드포인트**로 구현되어 있습니다:

| 단계 | 엔드포인트 | 설명 |
|-----|-----------|------|
| 1 | `GET /papers/{id}/try-semantic-scholar` | Semantic Scholar PDF 시도 |
| 2 | `GET /papers/{id}/try-arxiv` | arXiv PDF 시도 |
| 3 | `GET /papers/{id}/try-unpaywall` | Unpaywall (DOI) 시도 |
| 4 | `GET /papers/{id}/try-google-scholar` | Google Scholar 시도 |
| 5 | `GET /papers/{id}/try-google-search` | Google 검색 시도 |

**응답 형식** (공통):
```json
{
  "paper_id": "3e3f9411776a36572cd021f0f0f992029b9a6fd5",
  "pdf_found": true,
  "pdf_url": "https://arxiv.org/pdf/2402.12994",
  "source": "semantic_scholar",
  "local_path": "data/papers_pdf/3e3f9411776a36572cd021f0f0f992029b9a6fd5.pdf"
}
```

**실패 시** (404):
```json
{
  "detail": {
    "error": "PDF_NOT_FOUND",
    "message": "Semantic Scholar에 PDF 없음"
  }
}
```

---

## 🎯 n8n 노드 설정

### [1] Try Semantic Scholar

**HTTP Request 노드**
- Method: `GET`
- URL: `http://api:8000/api/v1/papers/{{ $json.id }}/try-semantic-scholar`
- Options → Response:
  - ✅ **Never Error** (404도 정상 처리)

### PDF Found? (If 노드)

**조건**:
- `{{ $json.pdf_found }}` == `true`

**분기**:
- ✅ True → `Extract PDF Text`
- ❌ False → `[2] Try arXiv`

### [2] Try arXiv

**HTTP Request 노드**
- Method: `GET`
- URL: `http://api:8000/api/v1/papers/{{ $('Split Papers').item.json.id }}/try-arxiv`
  - ⚠️ **주의**: `Split Papers` 노드의 원본 데이터 참조!
- Options → Response:
  - ✅ **Never Error**

### PDF Found (arXiv)? (If 노드)

**조건**:
- `{{ $json.pdf_found }}` == `true`

**분기**:
- ✅ True → `Extract PDF Text`
- ❌ False → `[3] Try Unpaywall`

### [3] Try Unpaywall

**HTTP Request 노드**
- Method: `GET`
- URL: `http://api:8000/api/v1/papers/{{ $('Split Papers').item.json.id }}/try-unpaywall`
- Options → Response:
  - ✅ **Never Error**

### [4] Try Google Scholar

**HTTP Request 노드**
- Method: `GET`
- URL: `http://api:8000/api/v1/papers/{{ $('Split Papers').item.json.id }}/try-google-scholar`
- Options → Response:
  - ✅ **Never Error**

### [5] Try Google Search

**HTTP Request 노드**
- Method: `GET`
- URL: `http://api:8000/api/v1/papers/{{ $('Split Papers').item.json.id }}/try-google-search`
- Options → Response:
  - ✅ **Never Error**

### Give Up (No PDF)

**Set 노드**
- `status`: `"pdf_not_found_anywhere"`
- `paper_id`: `{{ $('Split Papers').item.json.id }}`

---

## 🚀 실행 방법

### 1. n8n 워크플로우 임포트

1. n8n UI 접속: http://localhost:5678
2. **Workflows** → **Import from File**
3. `My workflow.json` 선택
4. **Import** 클릭

### 2. OpenAI API Key 설정

1. **Credentials** → **Add Credential**
2. **OpenAI** 선택
3. API Key 입력
4. **Call OpenAI** 노드에서 Credential 선택

### 3. 파라미터 설정

**Input Parameters 노드**에서 수정:
- `keyword`: 검색 키워드 (예: "gnn recommendation system")
- `year_from`: 시작 연도 (예: 2024)
- `year_to`: 종료 연도 (예: 2025)
- `limit`: 논문 개수 (예: 2)

### 4. 실행

1. **Start Research** 노드 클릭
2. **Execute Workflow** 클릭
3. 각 노드의 실행 결과를 시각적으로 확인!

---

## 📈 실행 결과 확인

### 성공 케이스

```
[1] Try Semantic Scholar ✅
  → PDF Found? ✅
  → Extract PDF Text ✅
  → Call OpenAI ✅
  → Save Summary ✅
```

### 폭포수 검색 케이스

```
[1] Try Semantic Scholar ❌ (404)
  → [2] Try arXiv ❌ (404)
  → [3] Try Unpaywall ❌ (404)
  → [4] Try Google Scholar ✅
  → Extract PDF Text ✅
  → Call OpenAI ✅
  → Save Summary ✅
```

### 완전 실패 케이스

```
[1] Try Semantic Scholar ❌
  → [2] Try arXiv ❌
  → [3] Try Unpaywall ❌
  → [4] Try Google Scholar ❌
  → [5] Try Google Search ❌
  → Give Up (No PDF) 🚫
```

---

## 💾 저장 위치

- **PDF 파일**: `data/papers_pdf/{paper_id}.pdf`
- **논문 요약**: `data/paper_summaries/{paper_id}.json`
- **캐시**: `data/papers_cache.json`

---

## 🔍 디버깅 팁

### 1. API 로그 확인
```bash
docker logs research-assistant-api --tail 50
```

### 2. 특정 논문 PDF 수동 테스트
```bash
# Semantic Scholar 시도
curl "http://localhost:8000/api/v1/papers/{paper_id}/try-semantic-scholar"

# arXiv 시도
curl "http://localhost:8000/api/v1/papers/{paper_id}/try-arxiv"
```

### 3. n8n 노드 데이터 확인

각 노드 클릭 → **Output** 탭에서 JSON 데이터 확인

---

## 🎨 워크플로우 시각화

```
Start → Input → Search → Split
                            ↓
                    [1] Semantic Scholar
                            ↓
                      PDF Found? ─── Yes → Extract → OpenAI → Save
                            ↓ No
                       [2] arXiv
                            ↓
                      PDF Found? ─── Yes → Extract → OpenAI → Save
                            ↓ No
                     [3] Unpaywall
                            ↓
                      PDF Found? ─── Yes → Extract → OpenAI → Save
                            ↓ No
                   [4] Google Scholar
                            ↓
                      PDF Found? ─── Yes → Extract → OpenAI → Save
                            ↓ No
                   [5] Google Search
                            ↓
                      PDF Found? ─── Yes → Extract → OpenAI → Save
                            ↓ No
                      Give Up 🚫
```

---

## ⚡ 성능 최적화

### 1. 로컬 캐시 활용

이미 다운로드한 PDF는 다시 다운로드하지 않습니다!

### 2. Rate Limit 대응

- Semantic Scholar: 5,000 req/5min (API Key)
- Google Scholar/Search: 요청 간격 자동 조절

### 3. 병렬 처리

`Split Papers` 노드가 각 논문을 병렬로 처리합니다!

---

## 🆘 문제 해결

### Q: "PDF_NOT_FOUND" 에러가 계속 나와요
**A**: 모든 소스를 시도했지만 PDF를 찾지 못한 경우입니다. 수동으로 PDF를 `data/papers_pdf/{paper_id}.pdf`에 추가하세요.

### Q: Google Scholar/Search가 작동하지 않아요
**A**: 봇 차단일 수 있습니다. 잠시 후 다시 시도하거나, VPN을 사용하세요.

### Q: OpenAI 요금이 걱정돼요
**A**: `gpt-4o-mini` 모델은 매우 저렴합니다 (~$0.0001/논문). 하루 100편 분석해도 $0.01 미만!

---

## 📚 추가 자료

- [n8n 공식 문서](https://docs.n8n.io)
- [Semantic Scholar API](https://api.semanticscholar.org)
- [OpenAI API 문서](https://platform.openai.com/docs)

---

**만든이**: AI Research Assistant
**버전**: Researcher Mindset v1.0
**날짜**: 2025-10-26
