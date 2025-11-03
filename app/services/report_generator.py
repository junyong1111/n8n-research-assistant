"""
연구 보고서 생성 서비스
마크다운 형식으로 주제별 논문 보고서 생성
"""
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger()


class ReportGenerator:
    """마크다운 보고서 생성기"""

    def __init__(self):
        self.data_dir = Path("data")
        self.reports_dir = Path("reports")
        self.knowledge_file = self.data_dir / "research_knowledge.json"
        self.summaries_dir = self.data_dir / "paper_summaries"

        # 디렉토리 생성
        self.reports_dir.mkdir(exist_ok=True)
        self.summaries_dir.mkdir(exist_ok=True)

    def generate_report(self, topic_name: str, save_to_file: bool = True) -> str:
        """
        주제별 연구 보고서 생성

        Args:
            topic_name: 주제명
            save_to_file: 파일로 저장 여부

        Returns:
            마크다운 형식의 보고서 문자열
        """
        logger.info(f"📊 보고서 생성 시작: {topic_name}")

        # 1. 지식 베이스 로드
        topic_data = self._load_topic_data(topic_name)
        if not topic_data:
            raise ValueError(f"주제를 찾을 수 없음: {topic_name}")

        # 2. 마크다운 생성
        markdown = self._generate_markdown(topic_name, topic_data)

        # 3. 파일 저장
        if save_to_file:
            filepath = self._save_report(topic_name, markdown)
            logger.info(f"✅ 보고서 저장: {filepath}")

        return markdown

    def _load_topic_data(self, topic_name: str) -> Optional[Dict]:
        """주제 데이터 로드"""
        if not self.knowledge_file.exists():
            logger.warning(f"⚠️ 지식 베이스 파일 없음: {self.knowledge_file}")
            return None

        with open(self.knowledge_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data.get("topics", {}).get(topic_name)

    def _load_paper_summary(self, paper_id: str) -> Optional[Dict]:
        """논문 요약 로드"""
        summary_file = self.summaries_dir / f"{paper_id}.json"
        if not summary_file.exists():
            return None

        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ 요약 로드 실패 ({paper_id}): {e}")
            return None

    def _generate_markdown(self, topic_name: str, topic_data: Dict) -> str:
        """마크다운 보고서 생성"""
        md = []

        # 헤더
        md.append(f"# {topic_name} 연구 보고서\n")
        md.append(f"**생성일**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md.append("---\n")

        # 요약 통계
        foundation = topic_data.get("foundation_papers", [])
        core = topic_data.get("core_papers", [])
        recent = topic_data.get("recent_papers", [])
        total = len(foundation) + len(core) + len(recent)

        md.append("## 📊 요약\n")
        md.append(f"- **총 논문 수**: {total}편\n")
        md.append(f"- **Foundation Papers**: {len(foundation)}편\n")
        md.append(f"- **Core Papers**: {len(core)}편\n")
        md.append(f"- **Recent Papers**: {len(recent)}편\n")

        # 지식 상태
        knowledge_state = topic_data.get("knowledge_state", {})
        if knowledge_state:
            state = knowledge_state.get("state", "beginner")
            progress = knowledge_state.get("progress_percentage", 0)
            md.append(f"- **지식 상태**: {state} ({progress:.1f}% 완료)\n")

        md.append("\n---\n")

        # Foundation Papers
        if foundation:
            md.append("## 🏛️ Foundation Papers (기초 논문)\n")
            md.append("*해당 분야의 기초가 되는 중요한 논문들*\n\n")
            for i, paper in enumerate(foundation, 1):
                md.extend(self._format_paper(i, paper))

        # Core Papers
        if core:
            md.append("## 🔬 Core Papers (핵심 논문)\n")
            md.append("*핵심 방법론 및 중요 기여를 담은 논문들*\n\n")
            for i, paper in enumerate(core, 1):
                md.extend(self._format_paper(i, paper))

        # Recent Papers
        if recent:
            md.append("## 🚀 Recent Papers (최신 논문)\n")
            md.append("*최근 1-2년 내 발표된 최신 연구*\n\n")
            for i, paper in enumerate(recent, 1):
                md.extend(self._format_paper(i, paper))

        # 푸터
        md.append("\n---\n")
        md.append("## 📝 메타데이터\n")
        md.append(f"- **마지막 업데이트**: {topic_data.get('last_updated', 'N/A')}\n")
        md.append(f"- **생성 도구**: n8n Research Assistant\n")
        md.append(f"- **데이터 소스**: Semantic Scholar API\n")

        return "".join(md)

    def _format_paper(self, index: int, paper: Dict) -> List[str]:
        """논문 정보를 마크다운으로 포맷"""
        md = []

        # 기본 정보
        title = paper.get("title", "제목 없음")
        authors = paper.get("authors", [])
        year = paper.get("year", "N/A")
        citations = paper.get("citations", 0)
        url = paper.get("url", "")
        venue = paper.get("venue", "")

        md.append(f"### {index}. {title}\n")

        if authors:
            if isinstance(authors, list):
                authors_str = ", ".join(authors[:3])
                if len(authors) > 3:
                    authors_str += f" 외 {len(authors) - 3}명"
            else:
                authors_str = str(authors)
            md.append(f"- **저자**: {authors_str}\n")

        md.append(f"- **연도**: {year}\n")

        if venue:
            md.append(f"- **출판**: {venue}\n")

        md.append(f"- **인용수**: {citations:,}회\n")

        if url:
            md.append(f"- **링크**: [{url}]({url})\n")

        # LLM 요약 추가
        paper_id = paper.get("id")
        if paper_id:
            summary = self._load_paper_summary(paper_id)
            if summary:
                md.append("\n**📝 요약**:\n")

                # 한국어 요약
                summary_ko = summary.get("summary_ko")
                if summary_ko:
                    md.append(f"{summary_ko}\n\n")

                # 핵심 기여
                contributions = summary.get("key_contributions", [])
                if contributions:
                    md.append("**핵심 기여**:\n")
                    for contrib in contributions:
                        md.append(f"- {contrib}\n")
                    md.append("\n")

                # 방법론
                methodology = summary.get("methodology")
                if methodology:
                    md.append(f"**방법론**: {methodology}\n\n")

                # 주요 결과
                results = summary.get("main_results")
                if results:
                    md.append(f"**주요 결과**: {results}\n\n")

                # 한계점
                limitations = summary.get("limitations")
                if limitations:
                    md.append(f"**한계점**: {limitations}\n\n")

                # 데이터셋
                dataset = summary.get("dataset")
                if dataset and dataset != "N/A":
                    md.append(f"**데이터셋**: {dataset}\n\n")

        md.append("---\n\n")
        return md

    def _save_report(self, topic_name: str, markdown: str) -> Path:
        """보고서를 파일로 저장"""
        # 파일명 생성 (공백 제거, 타임스탬프 추가)
        safe_name = topic_name.replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.md"
        filepath = self.reports_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)

        # 최신 버전도 별도 저장 (타임스탬프 없이)
        latest_filepath = self.reports_dir / f"{safe_name}_latest.md"
        with open(latest_filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)

        return filepath

    def list_reports(self) -> List[Dict]:
        """저장된 보고서 목록 조회"""
        reports = []

        if not self.reports_dir.exists():
            return reports

        for filepath in self.reports_dir.glob("*.md"):
            if "_latest" in filepath.name:
                continue  # latest 버전은 제외

            reports.append({
                "filename": filepath.name,
                "path": str(filepath),
                "size": filepath.stat().st_size,
                "created": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
            })

        # 최신순 정렬
        reports.sort(key=lambda x: x["created"], reverse=True)
        return reports

