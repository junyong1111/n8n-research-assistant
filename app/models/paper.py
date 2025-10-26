"""
논문 데이터 모델
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional


class PaperSearchRequest(BaseModel):
    """논문 검색 요청"""
    keyword: str = Field(..., description="검색 키워드")
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


class CitationNetworkRequest(BaseModel):
    """Citation Network 요청"""
    paper_id: str = Field(..., description="Seed 논문 ID")
    include_references: bool = Field(True, description="References 포함 여부")
    include_citations: bool = Field(True, description="Citations 포함 여부")
    max_references: int = Field(20, description="최대 References 수", ge=1, le=100)
    max_citations: int = Field(20, description="최대 Citations 수", ge=1, le=100)


class CitationNetworkResponse(BaseModel):
    """Citation Network 응답"""
    seed_paper: Paper = Field(..., description="Seed 논문")
    references: List[Paper] = Field([], description="이 논문이 인용한 논문들")
    citations: List[Paper] = Field([], description="이 논문을 인용한 논문들")
    total_references: int = Field(0, description="전체 References 수")
    total_citations: int = Field(0, description="전체 Citations 수")


class KnowledgeState(BaseModel):
    """지식 상태"""
    state: str = Field(..., description="beginner | intermediate | experienced")
    foundation_papers_read: int = Field(0, description="읽은 Foundation 논문 수")
    core_papers_read: int = Field(0, description="읽은 Core 논문 수")
    recent_papers_read: int = Field(0, description="읽은 Recent 논문 수")
    progress_percentage: float = Field(0.0, description="진행률 (%)")


class TopicKnowledge(BaseModel):
    """주제별 지식 상태"""
    topic_name: str = Field(..., description="주제명")
    knowledge_state: KnowledgeState = Field(..., description="지식 상태")
    foundation_papers: List[Paper] = Field([], description="Foundation 논문들")
    core_papers: List[Paper] = Field([], description="Core 논문들")
    recent_papers: List[Paper] = Field([], description="Recent 논문들")
    reading_order: List[str] = Field([], description="추천 읽기 순서 (paper IDs)")
    last_updated: str = Field(..., description="마지막 업데이트 시간")


class SimplePaperInfo(BaseModel):
    """간단한 논문 정보 (Agent 출력용)"""
    id: str = Field(..., description="논문 ID")
    title: str = Field(..., description="논문 제목")
    year: Optional[int] = Field(None, description="출판 연도")
    reason: str = Field("", description="분류/선정 이유")


class ResearchGapAnalysis(BaseModel):
    """Research Gap 분석 결과"""
    topic: str = Field(..., description="연구 주제")
    analyzed_papers_count: int = Field(..., description="분석한 논문 수")
    common_problems: List[str] = Field([], description="공통적으로 다루는 문제들")
    unsolved_problems: List[str] = Field([], description="미해결 문제들")
    recent_trends: List[str] = Field([], description="최근 트렌드")
    potential_research_directions: List[str] = Field([], description="잠재적 연구 방향")
    recommended_papers_to_read: List[str] = Field([], description="읽어야 할 논문 IDs")

