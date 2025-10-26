"""
Semantic Scholar API 클라이언트
공식 REST API를 사용한 논문 검색 서비스
"""
from typing import List, Dict, Optional
import requests
from app.utils.logger import get_logger, log_execution_time
from app.config import settings
import time
import json
import os
from pathlib import Path
from datetime import datetime

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

        # 캐시 및 PDF 저장 경로 설정
        self.cache_file = Path("data/papers_cache.json")
        self.pdf_dir = Path("data/papers_pdf")
        self._ensure_directories()

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
            "abstract": paper.get("abstract") or None,  # None을 명시적으로 허용
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

    @log_execution_time
    def get_citation_network(
        self,
        paper_id: str,
        max_references: int = 20,
        max_citations: int = 20,
        include_references: bool = True,
        include_citations: bool = True
    ) -> Dict:
        """
        논문의 Citation Network 가져오기 (References + Citations)

        Args:
            paper_id: Seed 논문 ID
            max_references: 최대 References 수
            max_citations: 최대 Citations 수
            include_references: References 포함 여부
            include_citations: Citations 포함 여부

        Returns:
            {
                "seed_paper": {...},
                "references": [...],
                "citations": [...],
                "total_references": int,
                "total_citations": int
            }
        """
        try:
            logger.info(f"🌳 Citation Network 구축 시작: {paper_id}")

            # 1. Seed 논문 정보 가져오기 (References + Citations 포함)
            fields = [
                "paperId", "title", "authors", "year", "venue",
                "citationCount", "url", "abstract", "externalIds",
                "openAccessPdf"
            ]

            if include_references:
                fields.append("references")
            if include_citations:
                fields.append("citations")

            url = f"{self.BASE_URL}/paper/{paper_id}"
            params = {"fields": ",".join(fields)}

            # API 요청 (재시도 로직)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.session.get(url, params=params, timeout=30)

                    # 429 Rate Limit 처리
                    if response.status_code == 429:
                        wait_time = (attempt + 1) * 5  # 5초, 10초, 15초
                        logger.warning(f"⏳ Rate Limit 도달. {wait_time}초 대기 중... (시도 {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    break  # 성공하면 종료

                except requests.exceptions.HTTPError as e:
                    if attempt == max_retries - 1:  # 마지막 시도
                        raise
                    logger.warning(f"Citation Network 요청 실패, 재시도 중... ({attempt + 1}/{max_retries})")
                    time.sleep(3)

            seed_data = response.json()

            # 2. Seed 논문 변환
            seed_paper = self._convert_paper_format(seed_data)

            # 3. References 처리 (상세 정보 + PDF 다운로드)
            references = []
            total_references = 0
            if include_references and "references" in seed_data:
                raw_references = seed_data["references"]
                total_references = len(raw_references)

                logger.info(f"🔄 References 상세 정보 조회 중... (최대 {max_references}개)")
                for idx, ref in enumerate(raw_references[:max_references], 1):
                    try:
                        if ref.get("paperId"):
                            # 상세 정보 조회 (캐싱 + PDF 다운로드)
                            detailed_paper = self.get_paper_details(ref["paperId"], download_pdf=True)
                            if detailed_paper:
                                references.append(detailed_paper)
                                logger.info(f"  [{idx}/{max_references}] ✅ {detailed_paper['title'][:50]}...")
                            else:
                                # 실패 시 기본 정보라도 저장
                                converted = self._convert_citation_item(ref)
                                references.append(converted)
                                logger.warning(f"  [{idx}/{max_references}] ⚠️ 기본 정보만 저장")

                            # Rate Limit 방지
                            time.sleep(0.5)
                    except Exception as e:
                        logger.warning(f"Reference 처리 실패: {e}")
                        continue

                logger.info(f"✅ References: {len(references)}/{total_references}개 완료")

            # 4. Citations 처리 (상세 정보 + PDF 다운로드)
            citations = []
            total_citations = 0
            if include_citations and "citations" in seed_data:
                raw_citations = seed_data["citations"]
                total_citations = len(raw_citations)

                logger.info(f"🔄 Citations 상세 정보 조회 중... (최대 {max_citations}개)")
                for idx, cit in enumerate(raw_citations[:max_citations], 1):
                    try:
                        if cit.get("paperId"):
                            # 상세 정보 조회 (캐싱 + PDF 다운로드)
                            detailed_paper = self.get_paper_details(cit["paperId"], download_pdf=True)
                            if detailed_paper:
                                citations.append(detailed_paper)
                                logger.info(f"  [{idx}/{max_citations}] ✅ {detailed_paper['title'][:50]}...")
                            else:
                                # 실패 시 기본 정보라도 저장
                                converted = self._convert_citation_item(cit)
                                citations.append(converted)
                                logger.warning(f"  [{idx}/{max_citations}] ⚠️ 기본 정보만 저장")

                            # Rate Limit 방지
                            time.sleep(0.5)
                    except Exception as e:
                        logger.warning(f"Citation 처리 실패: {e}")
                        continue

                logger.info(f"✅ Citations: {len(citations)}/{total_citations}개 완료")

            logger.info(f"🎉 Citation Network 구축 완료: Seed 1개 + Ref {len(references)}개 + Cit {len(citations)}개")

            return {
                "seed_paper": seed_paper,
                "references": references,
                "citations": citations,
                "total_references": total_references,
                "total_citations": total_citations
            }

        except Exception as e:
            logger.error(f"❌ Citation Network 구축 실패: {e}")
            raise

    def _convert_citation_item(self, item: Dict) -> Dict:
        """Citation/Reference 아이템을 표준 형식으로 변환"""
        authors = []
        for author in item.get("authors", []):
            if author.get("name"):
                authors.append(author["name"])

        external_ids = item.get("externalIds", {})
        doi = external_ids.get("DOI") if external_ids else None

        return {
            "id": item.get("paperId", ""),
            "title": item.get("title", ""),
            "authors": authors,
            "year": item.get("year"),
            "venue": item.get("venue", ""),
            "citations": item.get("citationCount", 0),
            "url": item.get("url", ""),
            "abstract": item.get("abstract"),
            "doi": doi,
            "pdf_url": None,  # Citation API에서는 제공 안됨
        }

    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_cache(self) -> Dict:
        """캐시 파일 로드"""
        if not self.cache_file.exists():
            return {"papers": {}, "last_updated": None, "cache_info": {"total_papers": 0, "total_pdfs": 0}}

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"캐시 로드 실패: {e}")
            return {"papers": {}, "last_updated": None, "cache_info": {"total_papers": 0, "total_pdfs": 0}}

    def _save_cache(self, cache: Dict):
        """캐시 파일 저장"""
        try:
            cache["last_updated"] = datetime.now().isoformat()
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"캐시 저장 실패: {e}")

    def get_paper_details(self, paper_id: str, download_pdf: bool = True) -> Optional[Dict]:
        """
        논문 상세 정보 조회 및 PDF 다운로드 (캐싱 포함)

        Args:
            paper_id: Semantic Scholar Paper ID
            download_pdf: PDF 다운로드 여부

        Returns:
            논문 상세 정보 (캐시 또는 API 조회)
        """
        try:
            # 1. 캐시 확인
            cache = self._load_cache()
            if paper_id in cache["papers"]:
                logger.info(f"📦 캐시에서 로드: {paper_id}")
                return cache["papers"][paper_id]

            # 2. API 조회
            logger.info(f"🔍 API 조회 시작: {paper_id}")
            fields = [
                "paperId", "title", "authors", "year", "venue",
                "citationCount", "url", "abstract", "externalIds",
                "openAccessPdf"
            ]

            url = f"{self.BASE_URL}/paper/{paper_id}"
            params = {"fields": ",".join(fields)}

            # Rate Limit 대응 재시도
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.session.get(url, params=params, timeout=30)

                    if response.status_code == 429:
                        wait_time = (attempt + 1) * 5
                        logger.warning(f"⏳ Rate Limit. {wait_time}초 대기... ({attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    break

                except requests.exceptions.HTTPError as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"재시도 중... ({attempt + 1}/{max_retries})")
                    time.sleep(3)

            paper_data = response.json()
            paper = self._convert_paper_format(paper_data)

            # 3. PDF 다운로드
            if download_pdf and paper.get("pdf_url"):
                pdf_path = self._download_pdf(paper_id, paper["pdf_url"])
                if pdf_path:
                    paper["local_pdf_path"] = str(pdf_path)
                    cache["cache_info"]["total_pdfs"] = cache["cache_info"].get("total_pdfs", 0) + 1

            # 4. 캐시 저장
            cache["papers"][paper_id] = paper
            cache["cache_info"]["total_papers"] = len(cache["papers"])
            self._save_cache(cache)

            logger.info(f"✅ 논문 조회 완료: {paper['title'][:60]}...")
            return paper

        except Exception as e:
            logger.error(f"❌ 논문 상세 조회 실패 ({paper_id}): {e}")
            return None

    def _download_pdf(self, paper_id: str, pdf_url: str) -> Optional[Path]:
        """
        PDF 다운로드

        Args:
            paper_id: 논문 ID
            pdf_url: PDF URL

        Returns:
            저장된 PDF 파일 경로
        """
        try:
            pdf_path = self.pdf_dir / f"{paper_id}.pdf"

            # 이미 존재하면 스킵
            if pdf_path.exists():
                logger.info(f"📄 PDF 이미 존재: {pdf_path.name}")
                return pdf_path

            logger.info(f"📥 PDF 다운로드 시작: {pdf_url}")
            response = self.session.get(pdf_url, timeout=60, stream=True)
            response.raise_for_status()

            # PDF 저장
            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = pdf_path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"✅ PDF 다운로드 완료: {pdf_path.name} ({file_size:.2f} MB)")
            return pdf_path

        except Exception as e:
            logger.error(f"❌ PDF 다운로드 실패 ({paper_id}): {e}")
            return None

