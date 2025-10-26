"""
논문 처리 API 엔드포인트
PDF 텍스트 추출, 요약 저장 등
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict
from pathlib import Path
import json
from datetime import datetime

from app.services.pdf_processor import PDFProcessor
from app.services.semantic_scholar import SemanticScholarService
from app.utils.logger import get_logger

logger = get_logger()
router = APIRouter()


class PaperSummaryRequest(BaseModel):
    """논문 요약 저장 요청"""
    paper_id: str = Field(..., description="논문 ID")
    summary: str = Field(..., description="논문 요약 (LLM 생성)")
    metadata: Optional[Dict] = Field(None, description="추가 메타데이터")


class FindPDFResponse(BaseModel):
    """PDF 찾기 응답"""
    paper_id: str
    pdf_found: bool
    pdf_url: Optional[str] = None
    source: Optional[str] = None  # "semantic_scholar" | "arxiv" | "unpaywall"
    local_path: Optional[str] = None


class ExtractTextResponse(BaseModel):
    """텍스트 추출 응답"""
    paper_id: str
    text_length: int
    num_pages: Optional[int] = None
    text: str
    pdf_info: Optional[Dict] = None


@router.get(
    "/papers/{paper_id}/find-pdf",
    summary="PDF 찾기",
    description="논문 ID로 PDF를 찾아서 다운로드 (Semantic Scholar → arXiv → Unpaywall)"
)
async def find_pdf(paper_id: str) -> FindPDFResponse:
    """
    PDF 찾기 및 다운로드 (다중 소스 시도 - 연구원처럼!)

    1. Local 확인
    2. Semantic Scholar
    3. arXiv
    4. Unpaywall
    5. Google Scholar
    6. Google 일반 검색
    """
    try:
        logger.info(f"🔍 PDF 찾기 시작 (다중 소스): {paper_id}")

        pdf_processor = PDFProcessor()
        semantic_service = SemanticScholarService()

        # 1. Semantic Scholar에서 논문 정보 조회
        paper = semantic_service.get_paper_details(paper_id, download_pdf=False)
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PAPER_NOT_FOUND", "message": f"논문을 찾을 수 없음: {paper_id}"}
            )

        # 2. 다중 소스에서 PDF 찾기
        title = paper.get("title", "")
        authors = paper.get("authors", [])
        doi = paper.get("doi")

        external_ids = paper.get("externalIds", {})
        arxiv_id = external_ids.get("ArXiv") if external_ids else None
        semantic_scholar_pdf = paper.get("pdf_url")

        pdf_path, source = pdf_processor.find_pdf_from_multiple_sources(
            paper_id=paper_id,
            title=title,
            authors=authors,
            doi=doi,
            arxiv_id=arxiv_id,
            semantic_scholar_pdf=semantic_scholar_pdf
        )

        if pdf_path:
            logger.info(f"✅ PDF 찾기 성공: {source}")
            return FindPDFResponse(
                paper_id=paper_id,
                pdf_found=True,
                pdf_url=semantic_scholar_pdf if source == "semantic_scholar" else None,
                source=source,
                local_path=str(pdf_path)
            )

        # 모든 소스에서 실패
        logger.warning(f"⚠️ 모든 소스에서 PDF 찾기 실패: {paper_id}")
        return FindPDFResponse(
            paper_id=paper_id,
            pdf_found=False,
            pdf_url=None,
            source=None,
            local_path=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ PDF 찾기 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "FIND_PDF_ERROR", "message": str(e)}
        )


@router.get(
    "/papers/{paper_id}/pdf-text",
    summary="PDF 텍스트 추출",
    description="PDF에서 전문 텍스트 추출 (LLM 요약용)"
)
async def extract_pdf_text(paper_id: str) -> ExtractTextResponse:
    """
    PDF 텍스트 추출

    1. 로컬에 PDF 있는지 확인
    2. 없으면 find-pdf 먼저 호출
    3. PDF 텍스트 추출
    """
    try:
        logger.info(f"📄 PDF 텍스트 추출 시작: {paper_id}")

        pdf_processor = PDFProcessor()

        # 1. PDF 경로 확인
        pdf_path = pdf_processor.get_pdf_path(paper_id)

        # 2. PDF 없으면 찾기
        if not pdf_path:
            logger.info(f"🔍 PDF 없음, 찾기 시도...")
            find_result = await find_pdf(paper_id)
            if not find_result.pdf_found or not find_result.local_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": "PDF_NOT_FOUND",
                        "message": f"PDF를 찾을 수 없음: {paper_id}",
                        "suggestion": "Abstract만 사용하거나 수동으로 PDF 추가 필요"
                    }
                )
            pdf_path = Path(find_result.local_path)

        # 3. 텍스트 추출
        text = pdf_processor.extract_text_from_pdf(pdf_path)
        if not text:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "TEXT_EXTRACTION_FAILED",
                    "message": "PDF 텍스트 추출 실패 (이미지 기반 PDF일 수 있음)"
                }
            )

        # 4. PDF 메타데이터
        pdf_info = pdf_processor.get_pdf_info(pdf_path)

        logger.info(f"✅ 텍스트 추출 완료: {len(text)} chars, {pdf_info.get('num_pages', 0)} pages")

        return ExtractTextResponse(
            paper_id=paper_id,
            text_length=len(text),
            num_pages=pdf_info.get("num_pages"),
            text=text,
            pdf_info=pdf_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 텍스트 추출 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "EXTRACT_TEXT_ERROR", "message": str(e)}
        )


@router.post(
    "/papers/summary",
    summary="논문 요약 저장",
    description="LLM이 생성한 논문 요약 저장"
)
async def save_paper_summary(request: PaperSummaryRequest):
    """
    논문 요약 저장

    data/paper_summaries/{paper_id}.json에 저장
    """
    try:
        logger.info(f"💾 요약 저장 시작: {request.paper_id}")

        # 저장 디렉토리 생성
        summary_dir = Path("data/paper_summaries")
        summary_dir.mkdir(parents=True, exist_ok=True)

        # 요약 데이터
        summary_data = {
            "paper_id": request.paper_id,
            "summary": request.summary,
            "metadata": request.metadata or {},
            "created_at": datetime.now().isoformat(),
            "summary_length": len(request.summary)
        }

        # 저장
        summary_path = summary_dir / f"{request.paper_id}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ 요약 저장 완료: {summary_path}")

        return {
            "message": "요약 저장 완료",
            "paper_id": request.paper_id,
            "summary_path": str(summary_path),
            "summary_length": len(request.summary)
        }

    except Exception as e:
        logger.error(f"❌ 요약 저장 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "SAVE_SUMMARY_ERROR", "message": str(e)}
        )


@router.get(
    "/papers/{paper_id}/summary",
    summary="논문 요약 조회",
    description="저장된 논문 요약 조회"
)
async def get_paper_summary(paper_id: str):
    """저장된 요약 조회"""
    try:
        summary_path = Path(f"data/paper_summaries/{paper_id}.json")

        if not summary_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "SUMMARY_NOT_FOUND", "message": f"요약을 찾을 수 없음: {paper_id}"}
            )

        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)

        return summary_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 요약 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "GET_SUMMARY_ERROR", "message": str(e)}
        )


# ============================================================
# 🔍 개별 PDF 검색 엔드포인트 (n8n 워크플로우용)
# ============================================================

@router.get(
    "/papers/{paper_id}/try-semantic-scholar",
    summary="[1단계] Semantic Scholar PDF 시도",
    description="Semantic Scholar에서 PDF 찾기"
)
async def try_semantic_scholar(paper_id: str) -> FindPDFResponse:
    """
    [연구원 사고 1단계] Semantic Scholar에서 PDF 찾기
    """
    try:
        logger.info(f"🔍 [1/5] Semantic Scholar 시도: {paper_id}")

        pdf_processor = PDFProcessor()
        semantic_service = SemanticScholarService()

        # 1. 로컬에 이미 있는지 확인 (실제로 읽을 수 있는지도 확인)
        local_path = pdf_processor.get_pdf_path(paper_id)
        if local_path:
            # 실제로 텍스트 추출이 가능한지 확인
            test_text = pdf_processor.extract_text_from_pdf(local_path)
            if test_text and len(test_text.strip()) > 100:
                logger.info(f"✅ [LOCAL] PDF 이미 존재하고 읽기 가능")
                return FindPDFResponse(
                    paper_id=paper_id,
                    pdf_found=True,
                    source="local",
                    local_path=str(local_path)
                )
            else:
                logger.warning(f"⚠️ [LOCAL] PDF 파일은 있지만 읽을 수 없음, 재다운로드 시도")
                # 손상된 파일 삭제
                local_path.unlink(missing_ok=True)

        # 2. Semantic Scholar에서 논문 정보 조회
        paper = semantic_service.get_paper_details(paper_id, download_pdf=False)
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PAPER_NOT_FOUND", "message": f"논문을 찾을 수 없음: {paper_id}"}
            )

        # 3. Semantic Scholar PDF URL 확인
        pdf_url = paper.get("pdf_url")
        if not pdf_url:
            logger.warning(f"⚠️ Semantic Scholar에 PDF 없음")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PDF_NOT_FOUND", "message": "Semantic Scholar에 PDF 없음"}
            )

        # 4. PDF 다운로드
        pdf_path = pdf_processor.download_pdf_from_url(paper_id, pdf_url)
        if not pdf_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "DOWNLOAD_FAILED", "message": "PDF 다운로드 실패"}
            )

        logger.info(f"✅ [Semantic Scholar] PDF 다운로드 완료")
        return FindPDFResponse(
            paper_id=paper_id,
            pdf_found=True,
            pdf_url=pdf_url,
            source="semantic_scholar",
            local_path=str(pdf_path)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Semantic Scholar 시도 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "SEMANTIC_SCHOLAR_ERROR", "message": str(e)}
        )


@router.get(
    "/papers/{paper_id}/try-arxiv",
    summary="[2단계] arXiv PDF 시도",
    description="arXiv에서 PDF 찾기"
)
async def try_arxiv(paper_id: str) -> FindPDFResponse:
    """
    [연구원 사고 2단계] arXiv에서 PDF 찾기
    """
    try:
        logger.info(f"🔍 [2/5] arXiv 시도: {paper_id}")

        pdf_processor = PDFProcessor()
        semantic_service = SemanticScholarService()

        # 1. 논문 정보 조회 (arXiv ID 필요)
        paper = semantic_service.get_paper_details(paper_id, download_pdf=False)
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PAPER_NOT_FOUND", "message": f"논문을 찾을 수 없음: {paper_id}"}
            )

        # 2. arXiv ID 확인
        external_ids = paper.get("externalIds", {})
        arxiv_id = external_ids.get("ArXiv") if external_ids else None

        if not arxiv_id:
            logger.warning(f"⚠️ arXiv ID 없음")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "ARXIV_ID_NOT_FOUND", "message": "arXiv ID 없음"}
            )

        # 3. arXiv PDF URL 찾기
        pdf_url = pdf_processor.find_pdf_from_arxiv(arxiv_id)
        if not pdf_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PDF_NOT_FOUND", "message": "arXiv에 PDF 없음"}
            )

        # 4. PDF 다운로드
        pdf_path = pdf_processor.download_pdf_from_url(paper_id, pdf_url)
        if not pdf_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "DOWNLOAD_FAILED", "message": "PDF 다운로드 실패"}
            )

        logger.info(f"✅ [arXiv] PDF 다운로드 완료")
        return FindPDFResponse(
            paper_id=paper_id,
            pdf_found=True,
            pdf_url=pdf_url,
            source="arxiv",
            local_path=str(pdf_path)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ arXiv 시도 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ARXIV_ERROR", "message": str(e)}
        )


@router.get(
    "/papers/{paper_id}/try-unpaywall",
    summary="[3단계] Unpaywall PDF 시도",
    description="DOI로 Unpaywall에서 PDF 찾기"
)
async def try_unpaywall(paper_id: str) -> FindPDFResponse:
    """
    [연구원 사고 3단계] Unpaywall에서 PDF 찾기
    """
    try:
        logger.info(f"🔍 [3/5] Unpaywall 시도: {paper_id}")

        pdf_processor = PDFProcessor()
        semantic_service = SemanticScholarService()

        # 1. 논문 정보 조회 (DOI 필요)
        paper = semantic_service.get_paper_details(paper_id, download_pdf=False)
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PAPER_NOT_FOUND", "message": f"논문을 찾을 수 없음: {paper_id}"}
            )

        # 2. DOI 확인
        doi = paper.get("doi")
        if not doi:
            logger.warning(f"⚠️ DOI 없음")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "DOI_NOT_FOUND", "message": "DOI 없음"}
            )

        # 3. Unpaywall PDF URL 찾기
        pdf_url = pdf_processor.find_pdf_from_doi(doi)
        if not pdf_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PDF_NOT_FOUND", "message": "Unpaywall에 PDF 없음"}
            )

        # 4. PDF 다운로드
        pdf_path = pdf_processor.download_pdf_from_url(paper_id, pdf_url)
        if not pdf_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "DOWNLOAD_FAILED", "message": "PDF 다운로드 실패"}
            )

        logger.info(f"✅ [Unpaywall] PDF 다운로드 완료")
        return FindPDFResponse(
            paper_id=paper_id,
            pdf_found=True,
            pdf_url=pdf_url,
            source="unpaywall",
            local_path=str(pdf_path)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unpaywall 시도 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "UNPAYWALL_ERROR", "message": str(e)}
        )


@router.get(
    "/papers/{paper_id}/try-google-scholar",
    summary="[4단계] Google Scholar PDF 시도",
    description="Google Scholar에서 PDF 찾기"
)
async def try_google_scholar(paper_id: str) -> FindPDFResponse:
    """
    [연구원 사고 4단계] Google Scholar에서 PDF 찾기
    """
    try:
        logger.info(f"🔍 [4/5] Google Scholar 시도: {paper_id}")

        pdf_processor = PDFProcessor()
        semantic_service = SemanticScholarService()

        # 1. 논문 정보 조회 (제목, 저자 필요)
        paper = semantic_service.get_paper_details(paper_id, download_pdf=False)
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PAPER_NOT_FOUND", "message": f"논문을 찾을 수 없음: {paper_id}"}
            )

        # 2. Google Scholar 검색
        title = paper.get("title", "")
        authors = paper.get("authors", [])

        pdf_url = pdf_processor.search_google_scholar(title, authors)
        if not pdf_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PDF_NOT_FOUND", "message": "Google Scholar에 PDF 없음"}
            )

        # 3. PDF 다운로드
        pdf_path = pdf_processor.download_pdf_from_url(paper_id, pdf_url)
        if not pdf_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "DOWNLOAD_FAILED", "message": "PDF 다운로드 실패"}
            )

        logger.info(f"✅ [Google Scholar] PDF 다운로드 완료")
        return FindPDFResponse(
            paper_id=paper_id,
            pdf_found=True,
            pdf_url=pdf_url,
            source="google_scholar",
            local_path=str(pdf_path)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Google Scholar 시도 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "GOOGLE_SCHOLAR_ERROR", "message": str(e)}
        )


@router.get(
    "/papers/{paper_id}/try-google-search",
    summary="[5단계] Google 검색 PDF 시도",
    description="Google 일반 검색으로 PDF 찾기"
)
async def try_google_search(paper_id: str) -> FindPDFResponse:
    """
    [연구원 사고 5단계] Google 일반 검색으로 PDF 찾기
    """
    try:
        logger.info(f"🔍 [5/5] Google 검색 시도: {paper_id}")

        pdf_processor = PDFProcessor()
        semantic_service = SemanticScholarService()

        # 1. 논문 정보 조회 (제목 필요)
        paper = semantic_service.get_paper_details(paper_id, download_pdf=False)
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PAPER_NOT_FOUND", "message": f"논문을 찾을 수 없음: {paper_id}"}
            )

        # 2. Google 검색
        title = paper.get("title", "")
        pdf_url = pdf_processor.search_by_title_google(title)
        if not pdf_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "PDF_NOT_FOUND", "message": "Google 검색에서 PDF 못 찾음"}
            )

        # 3. PDF 다운로드
        pdf_path = pdf_processor.download_pdf_from_url(paper_id, pdf_url)
        if not pdf_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "DOWNLOAD_FAILED", "message": "PDF 다운로드 실패"}
            )

        logger.info(f"✅ [Google Search] PDF 다운로드 완료")
        return FindPDFResponse(
            paper_id=paper_id,
            pdf_found=True,
            pdf_url=pdf_url,
            source="google_search",
            local_path=str(pdf_path)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Google 검색 시도 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "GOOGLE_SEARCH_ERROR", "message": str(e)}
        )

