"""
논문 데이터 모델
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional


class PaperSearchRequest(BaseModel):
    """논문 검색 요청"""
    keyword: str = Field(..., description="검색 키워드", example="transformer recommendation system")
    year_from: int = Field(2020, description="시작 연도", ge=1900, le=2025)
    year_to: int = Field(2025, description="종료 연도", ge=1900, le=2025)
    limit: int = Field(5, description="반환할 논문 수", ge=1, le=100)


class Paper(BaseModel):
    """논문 정보"""
    id: str = Field(..., description="논문 ID")
    title: str = Field(..., description="논문 제목")
    authors: List[str] = Field(..., description="저자 목록")
    year: Optional[int] = Field(None, description="출판 연도")
    venue: str = Field("", description="컨퍼런스/저널")
    citations: int = Field(0, description="인용 수")
    url: str = Field("", description="논문 URL")
    abstract: Optional[str] = Field(None, description="초록")
    doi: Optional[str] = Field(None, description="DOI")
    pdf_url: Optional[str] = Field(None, description="PDF URL")


class PaperSearchResponse(BaseModel):
    """논문 검색 응답"""
    query: str = Field(..., description="검색 키워드")
    year_range: str = Field(..., description="검색 연도 범위")
    total_results: int = Field(..., description="결과 논문 수")
    papers: List[Paper] = Field(..., description="논문 목록")


class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    details: Optional[str] = Field(None, description="상세 내용")

