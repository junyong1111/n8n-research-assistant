"""
논문 검색 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, status
from app.models.paper import (
    PaperSearchRequest, PaperSearchResponse, Paper, ErrorResponse,
    CitationNetworkRequest, CitationNetworkResponse
)
from app.services.semantic_scholar import SemanticScholarService
from app.utils.logger import get_logger

logger = get_logger()
router = APIRouter()


@router.post(
    "/search/papers",
    response_model=PaperSearchResponse,
    summary="논문 검색",
    description="키워드로 학술 논문을 검색합니다 (Semantic Scholar API 사용)"
)
async def search_papers(request: PaperSearchRequest):
    """
    논문 검색 API

    - **keyword**: 검색 키워드 (필수)
    - **year_from**: 시작 연도 (기본: 2020)
    - **year_to**: 종료 연도 (기본: 2025)
    - **limit**: 반환할 논문 수 (기본: 5, 최대: 100)

    Returns:
        검색된 논문 목록 (Citation 순 정렬)
    """
    try:
        logger.info(f"📚 논문 검색 요청: keyword={request.keyword}, year={request.year_from}-{request.year_to}")

        # Semantic Scholar 서비스 초기화
        service = SemanticScholarService()

        # 논문 검색
        papers = service.search_papers(
            keyword=request.keyword,
            year_from=request.year_from,
            year_to=request.year_to,
            limit=request.limit
        )

        # 응답 생성
        response = PaperSearchResponse(
            query=request.keyword,
            year_range=f"{request.year_from}-{request.year_to}",
            total_results=len(papers),
            papers=[Paper(**paper) for paper in papers]
        )

        logger.info(f"✅ 검색 완료: {len(papers)}개 논문")
        return response

    except Exception as e:
        logger.error(f"❌ 논문 검색 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "SEARCH_ERROR",
                "message": "논문 검색 중 오류가 발생했습니다",
                "details": str(e)
            }
        )


@router.get(
    "/search/papers/{paper_id}",
    response_model=Paper,
    summary="논문 상세 조회",
    description="논문 ID로 상세 정보를 조회합니다"
)
async def get_paper_details(paper_id: str):
    """
    논문 상세 정보 조회

    - **paper_id**: Semantic Scholar Paper ID

    Returns:
        논문 상세 정보
    """
    try:
        logger.info(f"📄 논문 상세 조회: {paper_id}")

        # Semantic Scholar 서비스 초기화
        service = SemanticScholarService()

        # 논문 조회
        paper = service.get_paper_by_id(paper_id)

        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "PAPER_NOT_FOUND",
                    "message": f"논문을 찾을 수 없습니다: {paper_id}",
                    "details": None
                }
            )

        logger.info(f"✅ 논문 조회 완료: {paper['title'][:50]}...")
        return Paper(**paper)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 논문 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "FETCH_ERROR",
                "message": "논문 조회 중 오류가 발생했습니다",
                "details": str(e)
            }
        )


@router.post(
    "/search/citation-network",
    response_model=CitationNetworkResponse,
    summary="Citation Network 구축",
    description="논문의 인용 관계망 구축 (References + Citations)"
)
async def get_citation_network(request: CitationNetworkRequest):
    """
    Citation Network 구축 API

    - **paper_id**: Seed 논문 ID (필수)
    - **include_references**: References 포함 여부 (기본: True)
    - **include_citations**: Citations 포함 여부 (기본: True)
    - **max_references**: 최대 References 수 (기본: 20)
    - **max_citations**: 최대 Citations 수 (기본: 20)

    Returns:
        Seed 논문 + References + Citations
    """
    try:
        logger.info(f"🌳 Citation Network 요청: paper_id={request.paper_id}")

        # Semantic Scholar 서비스 초기화
        service = SemanticScholarService()

        # Citation Network 구축
        network = service.get_citation_network(
            paper_id=request.paper_id,
            max_references=request.max_references,
            max_citations=request.max_citations,
            include_references=request.include_references,
            include_citations=request.include_citations
        )

        # 응답 생성
        response = CitationNetworkResponse(
            seed_paper=Paper(**network["seed_paper"]),
            references=[Paper(**p) for p in network["references"]],
            citations=[Paper(**p) for p in network["citations"]],
            total_references=network["total_references"],
            total_citations=network["total_citations"]
        )

        logger.info(f"✅ Citation Network 구축 완료: Ref {len(response.references)}개, Cit {len(response.citations)}개")
        return response

    except Exception as e:
        logger.error(f"❌ Citation Network 구축 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "CITATION_NETWORK_ERROR",
                "message": "Citation Network 구축 중 오류가 발생했습니다",
                "details": str(e)
            }
        )

