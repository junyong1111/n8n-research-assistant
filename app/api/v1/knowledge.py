"""
지식 상태 관리 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from app.models.paper import Paper, SimplePaperInfo, TopicKnowledge, KnowledgeState
from app.services.knowledge_manager import KnowledgeManager
from app.services.report_generator import ReportGenerator
from app.utils.logger import get_logger

logger = get_logger()
router = APIRouter()


def classify_paper_category(paper: Dict, current_year: int = 2025) -> Literal["foundation", "core", "recent"]:
    """
    논문을 자동으로 분류

    Args:
        paper: 논문 정보 (year, citations 필요)
        current_year: 현재 연도

    Returns:
        "foundation" | "core" | "recent"
    """
    year = paper.get("year", current_year)
    citations = paper.get("citations", 0)

    # 최신 논문 (최근 2년)
    if year >= current_year - 2:
        return "recent"

    # 기초 논문 (10년 이상 + 인용수 500+)
    if year <= current_year - 10 and citations >= 500:
        return "foundation"

    # 핵심 논문 (5년 이상 + 인용수 100+)
    if year <= current_year - 5 and citations >= 100:
        return "foundation"

    # 그 외는 core
    return "core"


class CreateTopicRequest(BaseModel):
    """주제 생성 요청"""
    topic_name: str = Field(..., description="주제명")
    knowledge_state: str = Field("beginner", description="초기 지식 상태 (beginner/intermediate/experienced)")


class AddPapersRequest(BaseModel):
    """논문 추가 요청"""
    topic_name: str = Field(..., description="주제명")
    papers: List[SimplePaperInfo] = Field(..., description="추가할 논문 리스트 (간단한 정보)")
    category: str = Field("recent", description="카테고리 (foundation/core/recent)")


class MarkReadRequest(BaseModel):
    """논문 읽음 표시 요청"""
    topic_name: str = Field(..., description="주제명")
    paper_id: str = Field(..., description="논문 ID")
    category: str = Field(..., description="카테고리 (foundation/core/recent)")


@router.get(
    "/knowledge/topics",
    summary="주제 목록 조회",
    description="저장된 모든 주제 목록 조회"
)
async def get_all_topics():
    """모든 주제 목록 조회"""
    try:
        manager = KnowledgeManager()
        topics = manager.get_all_topics()

        return {
            "total_topics": len(topics),
            "topics": topics
        }
    except Exception as e:
        logger.error(f"❌ 주제 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "FETCH_ERROR", "message": str(e)}
        )


@router.get(
    "/knowledge/topics/{topic_name}",
    summary="주제별 지식 상태 조회",
    description="특정 주제의 지식 상태 및 논문 목록 조회"
)
async def get_topic_knowledge(topic_name: str):
    """주제별 지식 상태 조회"""
    try:
        manager = KnowledgeManager()
        topic = manager.get_topic_knowledge(topic_name)

        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "TOPIC_NOT_FOUND", "message": f"주제를 찾을 수 없음: {topic_name}"}
            )

        return topic
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 주제 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "FETCH_ERROR", "message": str(e)}
        )


@router.post(
    "/knowledge/topics",
    summary="새 주제 생성",
    description="새로운 연구 주제 생성"
)
async def create_topic(request: CreateTopicRequest):
    """새 주제 생성"""
    try:
        manager = KnowledgeManager()
        topic = manager.create_topic(
            topic_name=request.topic_name,
            knowledge_state=request.knowledge_state
        )

        logger.info(f"✅ 주제 생성: {request.topic_name}")
        return topic
    except Exception as e:
        logger.error(f"❌ 주제 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "CREATE_ERROR", "message": str(e)}
        )


@router.post(
    "/knowledge/topics/papers",
    summary="논문 추가",
    description="주제에 논문 추가 (중복 자동 제거)"
)
async def add_papers_to_topic(request: AddPapersRequest):
    """주제에 논문 추가"""
    try:
        manager = KnowledgeManager()

        # SimplePaperInfo를 Paper 형식으로 변환 (누락 필드는 기본값)
        papers_dict = []
        for p in request.papers:
            paper_dict = {
                "id": p.id,
                "title": p.title,
                "authors": [],  # 기본값
                "year": p.year,
                "venue": "",
                "citations": 0,
                "url": "",
                "abstract": p.reason,  # reason을 abstract에 저장
                "doi": None,
                "pdf_url": None
            }
            papers_dict.append(paper_dict)

        topic = manager.add_papers_to_topic(
            topic_name=request.topic_name,
            papers=papers_dict,
            category=request.category
        )

        return {
            "message": f"논문 추가 완료",
            "topic": topic
        }
    except Exception as e:
        logger.error(f"❌ 논문 추가 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ADD_ERROR", "message": str(e)}
        )


@router.post(
    "/knowledge/topics/mark-read",
    summary="논문 읽음 표시",
    description="논문을 읽음으로 표시하고 진행률 업데이트"
)
async def mark_paper_as_read(request: MarkReadRequest):
    """논문 읽음 표시"""
    try:
        manager = KnowledgeManager()
        manager.mark_paper_as_read(
            topic_name=request.topic_name,
            paper_id=request.paper_id,
            category=request.category
        )

        # 업데이트된 주제 정보 반환
        topic = manager.get_topic_knowledge(request.topic_name)

        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "TOPIC_NOT_FOUND", "message": "주제를 찾을 수 없습니다"}
            )

        return {
            "message": "읽음 표시 완료",
            "progress": topic["knowledge_state"]["progress_percentage"]
        }
    except Exception as e:
        logger.error(f"❌ 읽음 표시 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "UPDATE_ERROR", "message": str(e)}
        )


@router.get(
    "/knowledge/topics/{topic_name}/unread",
    summary="읽지 않은 논문 조회",
    description="주제의 읽지 않은 논문 목록 조회"
)
async def get_unread_papers(topic_name: str):
    """읽지 않은 논문 조회"""
    try:
        manager = KnowledgeManager()
        unread = manager.get_unread_papers(topic_name)

        total_unread = sum(len(papers) for papers in unread.values())

        return {
            "topic_name": topic_name,
            "total_unread": total_unread,
            "unread_papers": unread
        }
    except Exception as e:
        logger.error(f"❌ 읽지 않은 논문 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "FETCH_ERROR", "message": str(e)}
        )


class AutoClassifyRequest(BaseModel):
    """논문 자동 분류 요청"""
    topic_name: str = Field(..., description="주제명")
    paper: Dict = Field(..., description="논문 정보 (id, title, year, citations 필요)")


@router.post(
    "/knowledge/classify-and-add",
    summary="논문 자동 분류 및 추가",
    description="논문을 자동으로 분류(Foundation/Core/Recent)하고 주제에 추가"
)
async def classify_and_add_paper(request: AutoClassifyRequest):
    """논문 자동 분류 및 추가"""
    try:
        # 1. 카테고리 자동 분류
        category = classify_paper_category(request.paper)

        logger.info(f"📊 논문 분류: {request.paper.get('title', 'Unknown')} → {category}")

        # 2. SimplePaperInfo 형식으로 변환
        simple_paper = SimplePaperInfo(
            id=request.paper.get("id", ""),
            title=request.paper.get("title", ""),
            year=request.paper.get("year", 2025),
            reason=f"자동 분류: {category}"
        )

        # 3. 주제에 추가
        manager = KnowledgeManager()
        paper_dict = {
            "id": simple_paper.id,
            "title": simple_paper.title,
            "authors": request.paper.get("authors", []),
            "year": simple_paper.year,
            "venue": request.paper.get("venue", ""),
            "citations": request.paper.get("citations", 0),
            "url": request.paper.get("url", ""),
            "abstract": request.paper.get("abstract", ""),
            "doi": request.paper.get("doi"),
            "pdf_url": request.paper.get("pdf_url")
        }

        topic = manager.add_papers_to_topic(
            topic_name=request.topic_name,
            papers=[paper_dict],
            category=category
        )

        return {
            "message": "논문 자동 분류 및 추가 완료",
            "paper_id": simple_paper.id,
            "category": category,
            "topic": topic
        }
    except Exception as e:
        logger.error(f"❌ 논문 자동 분류 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "CLASSIFY_ERROR", "message": str(e)}
        )


@router.get(
    "/knowledge/topics/{topic_name}/report",
    summary="주제별 연구 보고서 생성",
    description="마크다운 형식의 연구 보고서 생성 및 반환",
    response_class=PlainTextResponse
)
async def generate_topic_report(topic_name: str, save: bool = True):
    """주제별 연구 보고서 생성"""
    try:
        generator = ReportGenerator()
        markdown = generator.generate_report(topic_name, save_to_file=save)

        logger.info(f"✅ 보고서 생성 완료: {topic_name}")
        return markdown
    except ValueError as e:
        logger.error(f"❌ 주제를 찾을 수 없음: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "TOPIC_NOT_FOUND", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"❌ 보고서 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "REPORT_ERROR", "message": str(e)}
        )


@router.get(
    "/knowledge/reports",
    summary="저장된 보고서 목록 조회",
    description="생성된 모든 보고서 목록 반환"
)
async def list_reports():
    """저장된 보고서 목록 조회"""
    try:
        generator = ReportGenerator()
        reports = generator.list_reports()

        return {
            "total": len(reports),
            "reports": reports
        }
    except Exception as e:
        logger.error(f"❌ 보고서 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "LIST_ERROR", "message": str(e)}
        )

