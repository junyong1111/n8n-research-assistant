FROM python:3.12-slim

WORKDIR /app

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 프로젝트 파일 복사
COPY pyproject.toml uv.lock ./
COPY app ./app
COPY .env .env

# 의존성 설치
RUN uv sync --frozen

# 포트 노출
EXPOSE 8000

# 앱 실행
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

