# Logger 사용 가이드

## 🚀 빠른 시작

### 1. 기본 사용 (가장 간단)
```python
from app.utils.logger import get_logger

logger = get_logger()

logger.info("정보 로그")
logger.warning("경고 로그")
logger.error("에러 로그")
```

### 2. 커스텀 설정
```python
from app.utils.logger import LoggerSetup

logger = LoggerSetup.setup(
    log_dir="logs",
    log_file="my_service.log",
    rotation="10 MB",        # 10MB마다 새 파일
    retention="7 days",      # 7일간 보관
    level="INFO",           # 파일 로그 레벨
    console_level="DEBUG"   # 콘솔 로그 레벨
)

logger.info("커스텀 설정 완료!")
```

### 3. JSON 포맷 (구조화된 로그)
```python
from app.utils.logger import LoggerSetup

logger = LoggerSetup.setup(
    log_file="api.log",
    json_format=True  # JSON 직렬화
)

logger.bind(user_id=123, action="search").info("사용자 검색")
# {"time": "2025-10-19...", "level": "INFO", "message": "사용자 검색", "user_id": 123, "action": "search"}
```

## 🎯 데코레이터 활용

### 1. 실행 시간 로깅
```python
from app.utils.logger import log_execution_time

@log_execution_time
def search_papers(keyword):
    # ... 논문 검색 로직
    return results

# 로그 출력:
# 🚀 search_papers 시작
# ✅ search_papers 완료 (2.35초)
```

### 2. 예외 자동 로깅
```python
from app.utils.logger import log_exception

@log_exception
def risky_operation():
    # ... 위험한 작업
    pass

# 예외 발생 시 자동으로 스택 트레이스 로깅
```

### 3. 데코레이터 조합
```python
from app.utils.logger import log_execution_time, log_exception

@log_execution_time
@log_exception
def complex_task():
    # 실행 시간 + 예외 모두 로깅
    pass
```

## 📊 로그 파일 구조

```
logs/
├── app.log           # 일반 로그
├── error.log         # 에러 전용
└── *.log.YYYY-MM-DD  # 로테이션된 백업 파일
```

## 🎨 로그 레벨

- `DEBUG`: 상세한 디버깅 정보
- `INFO`: 일반 정보
- `WARNING`: 경고 메시지
- `ERROR`: 에러 발생
- `CRITICAL`: 치명적인 오류

## 💡 팁

### 컨텍스트 정보 추가
```python
logger.bind(request_id="abc123").info("API 호출")
```

### 예외 로깅
```python
try:
    risky_code()
except Exception as e:
    logger.exception("예외 발생")  # 자동으로 스택 트레이스 포함
```

### 조건부 로깅
```python
if condition:
    logger.debug("디버그 정보: {data}", data=my_data)
```

## 🔧 설정 옵션

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `log_dir` | "logs" | 로그 디렉토리 |
| `log_file` | "app.log" | 로그 파일명 |
| `rotation` | "10 MB" | 회전 크기/시간 |
| `retention` | "7 days" | 보관 기간 |
| `level` | "INFO" | 파일 로그 레벨 |
| `console_level` | "DEBUG" | 콘솔 로그 레벨 |
| `json_format` | False | JSON 포맷 사용 |

## 🎯 rotation 옵션

- `"10 MB"` - 10MB마다 회전
- `"100 KB"` - 100KB마다 회전
- `"1 day"` - 매일 자정에 회전
- `"12:00"` - 매일 정오에 회전
- `"1 week"` - 매주 회전

## 🎯 retention 옵션

- `"7 days"` - 7일 후 삭제
- `"1 week"` - 1주일 후 삭제
- `"30 days"` - 30일 후 삭제
- `10` - 최신 10개 파일만 유지

