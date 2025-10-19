# 🔑 API Key 설정 가이드

## 1. Semantic Scholar API Key 발급

### 📝 발급 방법

1. **웹사이트 접속**
   ```
   https://www.semanticscholar.org/product/api
   ```

2. **"Request API Access" 클릭**
   - 또는 직접 신청: https://www.semanticscholar.org/product/api#api-key-form

3. **정보 입력**
   - 이름
   - 이메일 주소
   - 사용 목적 (간단히 작성)
   - 예: "Academic research automation for personal use"

4. **이메일 확인**
   - 즉시 or 5분 내 API Key 수신
   - 제목: "Your Semantic Scholar API Key"

### 📊 무료 vs API Key

| 항목 | 무료 (No Key) | API Key |
|------|--------------|---------|
| 요금 | 💰 **무료** | 💰 **무료** |
| Rate Limit | 100 req / 5분 | **5,000 req / 5분** |
| 기능 | 전체 | 전체 |
| 추천 | ❌ | ✅ **강력 추천!** |

---

## 2. API Key 설정 방법

### 방법 1: .env 파일 사용 (추천) 🌟

1. **`.env` 파일 편집**
   ```bash
   # 프로젝트 루트 디렉토리에서
   nano .env
   # 또는
   code .env
   ```

2. **API Key 입력**
   ```bash
   # Semantic Scholar API
   SEMANTIC_SCHOLAR_API_KEY=your_actual_api_key_here
   ```

3. **저장 후 종료**

4. **확인**
   ```bash
   cat .env | grep SEMANTIC_SCHOLAR_API_KEY
   ```

### 방법 2: 코드에서 직접 설정

```python
from app.services.semantic_scholar import SemanticScholarService

# API Key를 직접 전달
service = SemanticScholarService(api_key="your_api_key_here")
```

⚠️ **주의**: 코드에 직접 입력하면 Git에 노출될 수 있습니다!

---

## 3. 설정 확인

### 테스트 실행

```bash
uv run python test_semantic_scholar.py
```

### 예상 출력

#### ✅ API Key가 설정된 경우
```
✅ API Key로 초기화 (5,000 req/5min) 🚀
```

#### ⚠️ API Key가 없는 경우
```
✅ 무료 버전으로 초기화 (100 req/5min) ⚠️
```

---

## 4. 보안 주의사항

### ✅ 해야 할 것
- ✅ `.env` 파일을 `.gitignore`에 추가 (이미 추가됨)
- ✅ API Key를 환경변수로 관리
- ✅ API Key를 절대 공개 저장소에 커밋하지 않기

### ❌ 하지 말아야 할 것
- ❌ 코드에 직접 하드코딩
- ❌ API Key를 스크린샷에 포함
- ❌ 공개 채팅/이슈에 API Key 공유

---

## 5. 문제 해결

### Q1: API Key 발급이 안 돼요
**A**: 이메일 스팸함을 확인하세요. 보통 5분 내 도착합니다.

### Q2: 429 Rate Limit 에러가 계속 발생해요
**A**:
1. API Key가 제대로 설정되었는지 확인
2. 로그에 "API Key로 초기화" 메시지 확인
3. 5분 대기 후 재시도

### Q3: .env 파일이 없어요
**A**:
```bash
cp .env.example .env
nano .env
```

### Q4: API Key가 인식되지 않아요
**A**:
1. `.env` 파일 위치 확인 (프로젝트 루트)
2. 환경변수 이름 확인: `SEMANTIC_SCHOLAR_API_KEY`
3. 앞뒤 공백 제거
4. 따옴표 없이 입력

---

## 6. 추가 API Key (나중에 필요)

### Anthropic Claude API
```bash
ANTHROPIC_API_KEY=sk-ant-xxx
```
- 논문 요약/분석에 사용
- https://console.anthropic.com/

### Notion API
```bash
NOTION_API_KEY=secret_xxx
NOTION_DATABASE_ID=xxx
```
- 논문 저장/관리에 사용
- https://www.notion.so/my-integrations

---

## 📞 도움이 필요하신가요?

- Semantic Scholar API 문서: https://api.semanticscholar.org/
- 이슈 제기: GitHub Issues

