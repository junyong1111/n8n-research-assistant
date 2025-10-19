"""
FastAPI 메인 애플리케이션
n8n-research-assistant API Server
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import search
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()

# FastAPI 앱 생성
app = FastAPI(
    title="n8n Research Assistant API",
    description="학술 논문 검색 및 분석 자동화 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(search.router, prefix="/api/v1", tags=["Search"])


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "n8n Research Assistant API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "environment": settings.ENVIRONMENT
    }


@app.get("/api/v1/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "has_api_key": bool(settings.SEMANTIC_SCHOLAR_API_KEY)
    }


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시"""
    logger.info("🚀 n8n Research Assistant API 시작")
    logger.info(f"환경: {settings.ENVIRONMENT}")
    if settings.SEMANTIC_SCHOLAR_API_KEY:
        logger.info("✅ Semantic Scholar API Key 로드 완료")
    else:
        logger.warning("⚠️ Semantic Scholar API Key 없음 (무료 버전)")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시"""
    logger.info("🛑 n8n Research Assistant API 종료")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )
