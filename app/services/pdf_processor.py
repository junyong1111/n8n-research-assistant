"""
PDF 처리 서비스
PDF 다운로드, 텍스트 추출, 메타데이터 파싱
"""
from typing import Optional, Dict
from pathlib import Path
import requests
import PyPDF2
import pdfplumber
from app.utils.logger import get_logger

logger = get_logger()


class PDFProcessor:
    """PDF 처리 클래스"""

    def __init__(self, pdf_dir: str = "data/papers_pdf"):
        """
        초기화

        Args:
            pdf_dir: PDF 저장 디렉토리
        """
        self.pdf_dir = Path(pdf_dir)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

    def extract_text_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """
        PDF에서 텍스트 추출

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            추출된 텍스트 (실패 시 None)
        """
        try:
            logger.info(f"📄 PDF 텍스트 추출 시작: {pdf_path.name}")

            # 방법 1: pdfplumber (더 정확함)
            try:
                text = self._extract_with_pdfplumber(pdf_path)
                if text and len(text.strip()) > 100:
                    logger.info(f"✅ pdfplumber로 추출 완료: {len(text)} chars")
                    return text
            except Exception as e:
                logger.warning(f"pdfplumber 실패: {e}")

            # 방법 2: PyPDF2 (fallback)
            try:
                text = self._extract_with_pypdf2(pdf_path)
                if text and len(text.strip()) > 100:
                    logger.info(f"✅ PyPDF2로 추출 완료: {len(text)} chars")
                    return text
            except Exception as e:
                logger.warning(f"PyPDF2 실패: {e}")

            logger.error("❌ 모든 추출 방법 실패")
            return None

        except Exception as e:
            logger.error(f"❌ PDF 텍스트 추출 실패: {e}")
            return None

    def _extract_with_pdfplumber(self, pdf_path: Path) -> str:
        """pdfplumber로 텍스트 추출"""
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)

    def _extract_with_pypdf2(self, pdf_path: Path) -> str:
        """PyPDF2로 텍스트 추출"""
        text_parts = []
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)

    def get_pdf_path(self, paper_id: str) -> Optional[Path]:
        """
        논문 ID로 PDF 경로 가져오기 (파일 크기도 확인)

        Args:
            paper_id: 논문 ID

        Returns:
            PDF 경로 (없거나 손상되면 None)
        """
        pdf_path = self.pdf_dir / f"{paper_id}.pdf"
        if pdf_path.exists():
            # 파일 크기 확인 (최소 1KB 이상)
            file_size = pdf_path.stat().st_size
            if file_size > 1024:
                return pdf_path
            else:
                logger.warning(f"⚠️ PDF 파일이 너무 작음 (손상 가능): {file_size} bytes")
                return None
        return None

    def download_pdf_from_url(self, paper_id: str, pdf_url: str) -> Optional[Path]:
        """
        URL에서 PDF 다운로드

        Args:
            paper_id: 논문 ID
            pdf_url: PDF URL

        Returns:
            저장된 PDF 경로 (실패 시 None)
        """
        try:
            pdf_path = self.pdf_dir / f"{paper_id}.pdf"

            # 이미 존재하면 스킵
            if pdf_path.exists():
                logger.info(f"📄 PDF 이미 존재: {pdf_path.name}")
                return pdf_path

            logger.info(f"📥 PDF 다운로드 시작: {pdf_url}")
            response = requests.get(pdf_url, timeout=60, stream=True)
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

    def find_pdf_from_arxiv(self, arxiv_id: str) -> Optional[str]:
        """
        arXiv ID로 PDF URL 찾기

        Args:
            arxiv_id: arXiv ID (예: 2301.12345)

        Returns:
            PDF URL (실패 시 None)
        """
        try:
            # arXiv ID 정규화
            arxiv_id = arxiv_id.replace("arXiv:", "").strip()
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            # HEAD 요청으로 존재 확인
            response = requests.head(pdf_url, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ arXiv PDF 발견: {pdf_url}")
                return pdf_url

            logger.warning(f"⚠️ arXiv PDF 없음: {arxiv_id}")
            return None

        except Exception as e:
            logger.error(f"❌ arXiv PDF 검색 실패: {e}")
            return None

    def find_pdf_from_doi(self, doi: str) -> Optional[str]:
        """
        DOI로 Unpaywall API를 통해 PDF URL 찾기

        Args:
            doi: DOI (예: 10.1145/3589334.3645598)

        Returns:
            PDF URL (실패 시 None)
        """
        try:
            # Unpaywall API (무료, Open Access PDF만)
            email = "research@example.com"  # 필수 (정책상)
            api_url = f"https://api.unpaywall.org/v2/{doi}?email={email}"

            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()

                # Open Access PDF URL 찾기
                if data.get("is_oa") and data.get("best_oa_location"):
                    pdf_url = data["best_oa_location"].get("url_for_pdf")
                    if pdf_url:
                        logger.info(f"✅ Unpaywall PDF 발견: {pdf_url}")
                        return pdf_url

            logger.warning(f"⚠️ Unpaywall PDF 없음: {doi}")
            return None

        except Exception as e:
            logger.error(f"❌ Unpaywall 검색 실패: {e}")
            return None

    def search_google_scholar(self, title: str, authors: Optional[list] = None) -> Optional[str]:
        """
        Google Scholar에서 PDF 링크 찾기

        Args:
            title: 논문 제목
            authors: 저자 리스트 (선택)

        Returns:
            PDF URL (실패 시 None)
        """
        try:
            import urllib.parse
            from bs4 import BeautifulSoup

            # 검색 쿼리 생성
            query = title
            if authors and len(authors) > 0:
                query += f" {authors[0]}"

            encoded_query = urllib.parse.quote(query)
            search_url = f"https://scholar.google.com/scholar?q={encoded_query}"

            # User-Agent 설정 (봇 차단 방지)
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            if response.status_code != 200:
                logger.warning(f"⚠️ Google Scholar 접근 실패: {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # PDF 링크 찾기 ([PDF] 링크)
            for link in soup.find_all('a'):
                href = link.get('href', '')
                text = link.get_text()

                if '[PDF]' in text and href and isinstance(href, str):
                    logger.info(f"✅ Google Scholar PDF 발견: {href}")
                    return href

            logger.warning(f"⚠️ Google Scholar에서 PDF 못 찾음: {title[:50]}...")
            return None

        except Exception as e:
            logger.error(f"❌ Google Scholar 검색 실패: {e}")
            return None

    def search_by_title_google(self, title: str) -> Optional[str]:
        """
        구글 검색으로 논문 제목 + PDF 검색

        Args:
            title: 논문 제목

        Returns:
            PDF URL (실패 시 None)
        """
        try:
            import urllib.parse
            from bs4 import BeautifulSoup

            # "논문제목 pdf" 검색
            query = f'"{title}" filetype:pdf'
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://www.google.com/search?q={encoded_query}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            if response.status_code != 200:
                logger.warning(f"⚠️ Google 검색 실패: {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # PDF 링크 찾기
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if href and isinstance(href, str) and '.pdf' in href.lower() and 'http' in href:
                    # URL 정제
                    if 'url?q=' in href:
                        pdf_url = href.split('url?q=')[1].split('&')[0]
                        pdf_url = urllib.parse.unquote(pdf_url)
                    else:
                        pdf_url = href

                    logger.info(f"✅ Google 검색으로 PDF 발견: {pdf_url}")
                    return pdf_url

            logger.warning(f"⚠️ Google 검색에서 PDF 못 찾음: {title[:50]}...")
            return None

        except Exception as e:
            logger.error(f"❌ Google 검색 실패: {e}")
            return None

    def find_pdf_from_multiple_sources(
        self,
        paper_id: str,
        title: str,
        authors: Optional[list] = None,
        doi: Optional[str] = None,
        arxiv_id: Optional[str] = None,
        semantic_scholar_pdf: Optional[str] = None
    ) -> tuple[Optional[Path], Optional[str]]:
        """
        여러 소스에서 PDF 찾기 (연구원처럼 끝까지 시도!)

        Args:
            paper_id: 논문 ID
            title: 논문 제목
            authors: 저자 리스트
            doi: DOI
            arxiv_id: arXiv ID
            semantic_scholar_pdf: Semantic Scholar PDF URL

        Returns:
            (PDF 경로, 소스명) 튜플
        """
        logger.info(f"🔍 PDF 찾기 시작 (다중 소스): {title[:50]}...")

        # 1. 이미 로컬에 있는지 확인
        local_path = self.get_pdf_path(paper_id)
        if local_path:
            logger.info(f"✅ [LOCAL] PDF 이미 존재")
            return local_path, "local"

        # 2. Semantic Scholar PDF
        if semantic_scholar_pdf:
            logger.info(f"🔍 [1/5] Semantic Scholar 시도...")
            pdf_path = self.download_pdf_from_url(paper_id, semantic_scholar_pdf)
            if pdf_path:
                return pdf_path, "semantic_scholar"

        # 3. arXiv
        if arxiv_id:
            logger.info(f"🔍 [2/5] arXiv 시도...")
            pdf_url = self.find_pdf_from_arxiv(arxiv_id)
            if pdf_url:
                pdf_path = self.download_pdf_from_url(paper_id, pdf_url)
                if pdf_path:
                    return pdf_path, "arxiv"

        # 4. Unpaywall (DOI)
        if doi:
            logger.info(f"🔍 [3/5] Unpaywall 시도...")
            pdf_url = self.find_pdf_from_doi(doi)
            if pdf_url:
                pdf_path = self.download_pdf_from_url(paper_id, pdf_url)
                if pdf_path:
                    return pdf_path, "unpaywall"

        # 5. Google Scholar
        logger.info(f"🔍 [4/5] Google Scholar 시도...")
        pdf_url = self.search_google_scholar(title, authors)
        if pdf_url:
            pdf_path = self.download_pdf_from_url(paper_id, pdf_url)
            if pdf_path:
                return pdf_path, "google_scholar"

        # 6. Google 일반 검색
        logger.info(f"🔍 [5/5] Google 검색 시도...")
        pdf_url = self.search_by_title_google(title)
        if pdf_url:
            pdf_path = self.download_pdf_from_url(paper_id, pdf_url)
            if pdf_path:
                return pdf_path, "google_search"

        # 모든 방법 실패
        logger.error(f"❌ 모든 소스에서 PDF 찾기 실패: {title[:50]}...")
        return None, None

    def get_pdf_info(self, pdf_path: Path) -> Dict:
        """
        PDF 메타데이터 가져오기

        Args:
            pdf_path: PDF 경로

        Returns:
            메타데이터 딕셔너리
        """
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                info = reader.metadata or {}

                return {
                    "num_pages": len(reader.pages),
                    "title": info.get("/Title", ""),
                    "author": info.get("/Author", ""),
                    "subject": info.get("/Subject", ""),
                    "creator": info.get("/Creator", ""),
                    "producer": info.get("/Producer", ""),
                }
        except Exception as e:
            logger.error(f"PDF 메타데이터 추출 실패: {e}")
            return {}

