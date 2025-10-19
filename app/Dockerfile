FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성 + 한글 폰트
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates wget gnupg \
      fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# uv 설치 및 의존성 설  치
RUN uv sync --prod

# 앱 실행
EXPOSE 8000
CMD ["uv","run","uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]