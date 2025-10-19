"""
Semantic Scholar API 클라이언트
공식 REST API를 사용한 논문 검색 서비스
"""
from typing import List, Dict, Optional
import requests
from app.utils.logger import get_logger, log_execution_time
from app.config import settings
import time

logger = get_logger()


class SemanticScholarService:
    """Semantic Scholar API 서비스 클래스"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: Optional[str] = None):
        """
        초기화

        Args:
            api_key: Semantic Scholar API Key (선택)
                    None이면 환경변수(.env)에서 자동으로 읽음
                    없으면: 100 requests/5분
                    있으면: 5,000 requests/5분
        """
        # API Key 우선순위: 파라미터 > 환경변수
        self.api_key = api_key or settings.SEMANTIC_SCHOLAR_API_KEY
        self.session = requests.Session()

        # 기본 헤더 설정 (User-Agent 필수!)
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json"
        })

        # API Key가 있으면 헤더에 추가
        if self.api_key:
            self.session.headers.update({"x-api-key": self.api_key})
            logger.info("✅ API Key로 초기화 (5,000 req/5min) 🚀")
        else:
            logger.info("✅ 무료 버전으로 초기화 (100 req/5min) ⚠️")

    @log_execution_time
    def search_papers(
        self,
        keyword: str,
        year_from: int = 2024,
        year_to: int = 2025,
        limit: int = 5,
        fields: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        키워드로 논문 검색

        Args:
            keyword: 검색 키워드
            year_from: 시작 연도
            year_to: 종료 연도
            limit: 반환할 논문 수 (최대 100)
            fields: 가져올 필드 리스트

        Returns:
            논문 정보 리스트
        """
        try:
            logger.info(f"📚 논문 검색 시작: keyword='{keyword}', year={year_from}-{year_to}")

            # 기본 필드 설정
            if fields is None:
                fields = [
                    "paperId",
                    "title",
                    "authors",
                    "year",
                    "venue",
                    "citationCount",
                    "url",
                    "abstract",
                    "externalIds",
                    "openAccessPdf"
                ]

            # API 엔드포인트
            url = f"{self.BASE_URL}/paper/search"

            # 파라미터 설정
            params = {
                "query": keyword,
                "year": f"{year_from}-{year_to}",
                "limit": min(limit, 100),  # 최대 100
                "fields": ",".join(fields)
            }

            # API 요청 (재시도 로직)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.session.get(url, params=params, timeout=30)

                    # 429 Rate Limit 처리
                    if response.status_code == 429:
                        wait_time = (attempt + 1) * 10  # 10초, 20초, 30초
                        logger.warning(f"⏳ Rate Limit 도달. {wait_time}초 대기 중... (시도 {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    break  # 성공하면 종료

                except requests.exceptions.HTTPError as e:
                    if attempt == max_retries - 1:  # 마지막 시도
                        raise
                    logger.warning(f"요청 실패, 재시도 중... ({attempt + 1}/{max_retries})")
                    time.sleep(5)

            data = response.json()
            papers = data.get("data", [])

            if not papers:
                logger.warning("검색 결과가 없습니다.")
                return []

            # 논문 정보 변환
            result_papers = []
            for paper in papers:
                try:
                    converted = self._convert_paper_format(paper)
                    result_papers.append(converted)
                    logger.info(f"✅ [{len(result_papers)}] {converted['title'][:60]}... (인용: {converted['citations']})")
                except Exception as e:
                    logger.warning(f"논문 변환 중 오류: {e}")
                    continue

            # Citation 수 기준 정렬
            result_papers.sort(key=lambda x: x.get('citations', 0), reverse=True)

            logger.info(f"🎉 검색 완료: 총 {len(result_papers)}개 논문")
            return result_papers

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API 요청 실패: {e}")
            raise Exception(f"Semantic Scholar API 오류: {str(e)}")
        except Exception as e:
            logger.error(f"❌ 논문 검색 실패: {e}")
            raise

    def _convert_paper_format(self, paper: Dict) -> Dict:
        """Semantic Scholar 응답을 표준 형식으로 변환"""

        # 저자 리스트 추출
        authors = []
        for author in paper.get("authors", []):
            if author.get("name"):
                authors.append(author["name"])

        # DOI 추출
        external_ids = paper.get("externalIds", {})
        doi = external_ids.get("DOI")

        # PDF URL 추출
        pdf_url = None
        open_access = paper.get("openAccessPdf")
        if open_access and open_access.get("url"):
            pdf_url = open_access["url"]

        return {
            "id": paper.get("paperId", ""),
            "title": paper.get("title", ""),
            "authors": authors,
            "year": paper.get("year"),
            "venue": paper.get("venue", ""),
            "citations": paper.get("citationCount", 0),
            "url": paper.get("url", ""),
            "abstract": paper.get("abstract", ""),
            "doi": doi,
            "pdf_url": pdf_url,
        }

    def get_paper_by_id(self, paper_id: str, fields: Optional[List[str]] = None) -> Optional[Dict]:
        """
        논문 ID로 상세 정보 조회

        Args:
            paper_id: Semantic Scholar Paper ID
            fields: 가져올 필드 리스트

        Returns:
            논문 정보
        """
        try:
            logger.info(f"논문 상세 정보 조회: {paper_id}")

            # 기본 필드
            if fields is None:
                fields = [
                    "paperId", "title", "authors", "year", "venue",
                    "citationCount", "url", "abstract", "externalIds",
                    "openAccessPdf", "references", "citations"
                ]

            # API 요청
            url = f"{self.BASE_URL}/paper/{paper_id}"
            params = {"fields": ",".join(fields)}

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            paper = response.json()
            return self._convert_paper_format(paper)

        except Exception as e:
            logger.error(f"논문 조회 실패: {e}")
            return None

    def bulk_search_papers(
        self,
        keywords: List[str],
        year_from: int = 2024,
        year_to: int = 2025,
        limit_per_keyword: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        여러 키워드로 동시 검색

        Args:
            keywords: 검색 키워드 리스트
            year_from: 시작 연도
            year_to: 종료 연도
            limit_per_keyword: 키워드당 논문 수

        Returns:
            키워드별 논문 리스트
        """
        results = {}

        for keyword in keywords:
            try:
                papers = self.search_papers(
                    keyword=keyword,
                    year_from=year_from,
                    year_to=year_to,
                    limit=limit_per_keyword
                )
                results[keyword] = papers

                # Rate Limiting 방지 (무료: 100 req/5min)
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"키워드 '{keyword}' 검색 실패: {e}")
                results[keyword] = []

        return results

