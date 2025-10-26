"""
지식 상태 관리 서비스 (JSON 기반)
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger()


class KnowledgeManager:
    """논문 리서치 지식 상태 관리"""

    def __init__(self, storage_path: str = "data/research_knowledge.json"):
        """
        초기화

        Args:
            storage_path: JSON 저장 경로
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # 파일이 없으면 초기화
        if not self.storage_path.exists():
            self._initialize_storage()

        logger.info(f"✅ Knowledge Manager 초기화: {self.storage_path}")

    def _initialize_storage(self):
        """빈 저장소 초기화"""
        initial_data = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "topics": {}
        }
        self._save_data(initial_data)
        logger.info("📁 새 지식 저장소 생성")

    def _load_data(self) -> Dict:
        """JSON 데이터 로드"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ 데이터 로드 실패: {e}")
            return {"version": "1.0", "topics": {}}

    def _save_data(self, data: Dict):
        """JSON 데이터 저장"""
        try:
            data["last_updated"] = datetime.now().isoformat()
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("💾 데이터 저장 완료")
        except Exception as e:
            logger.error(f"❌ 데이터 저장 실패: {e}")
            raise

    def get_topic_knowledge(self, topic_name: str) -> Optional[Dict]:
        """
        주제별 지식 상태 조회

        Args:
            topic_name: 주제명 (예: "gnn_recommendation")

        Returns:
            주제 지식 정보 또는 None
        """
        data = self._load_data()
        topic_key = self._normalize_topic_name(topic_name)
        return data["topics"].get(topic_key)

    def create_topic(self, topic_name: str, knowledge_state: str = "beginner") -> Dict:
        """
        새 주제 생성

        Args:
            topic_name: 주제명
            knowledge_state: 초기 지식 상태 (beginner/intermediate/experienced)

        Returns:
            생성된 주제 정보
        """
        data = self._load_data()
        topic_key = self._normalize_topic_name(topic_name)

        if topic_key in data["topics"]:
            logger.warning(f"⚠️ 주제가 이미 존재함: {topic_name}")
            return data["topics"][topic_key]

        new_topic = {
            "topic_name": topic_name,
            "knowledge_state": {
                "state": knowledge_state,
                "foundation_papers_read": 0,
                "core_papers_read": 0,
                "recent_papers_read": 0,
                "progress_percentage": 0.0
            },
            "foundation_papers": [],
            "core_papers": [],
            "recent_papers": [],
            "reading_order": [],
            "last_updated": datetime.now().isoformat(),
            "search_history": []
        }

        data["topics"][topic_key] = new_topic
        self._save_data(data)

        logger.info(f"✅ 새 주제 생성: {topic_name} (상태: {knowledge_state})")
        return new_topic

    def add_papers_to_topic(
        self,
        topic_name: str,
        papers: List[Dict],
        category: str = "recent"  # foundation/core/recent
    ) -> Dict:
        """
        주제에 논문 추가

        Args:
            topic_name: 주제명
            papers: 논문 리스트
            category: 카테고리 (foundation/core/recent)

        Returns:
            업데이트된 주제 정보
        """
        data = self._load_data()
        topic_key = self._normalize_topic_name(topic_name)

        # 주제가 없으면 생성
        if topic_key not in data["topics"]:
            data["topics"][topic_key] = self.create_topic(topic_name)

        topic = data["topics"][topic_key]
        category_key = f"{category}_papers"

        if category_key not in topic:
            logger.error(f"❌ 잘못된 카테고리: {category}")
            return topic

        # 중복 제거 (paper_id 기준)
        existing_ids = {p["id"] for p in topic[category_key]}
        new_papers = [p for p in papers if p["id"] not in existing_ids]

        if new_papers:
            topic[category_key].extend(new_papers)
            topic["last_updated"] = datetime.now().isoformat()
            self._save_data(data)
            logger.info(f"✅ 논문 {len(new_papers)}개 추가: {topic_name} > {category}")
        else:
            logger.info(f"ℹ️ 추가할 새 논문 없음 (모두 중복)")

        return topic

    def mark_paper_as_read(self, topic_name: str, paper_id: str, category: str):
        """논문을 읽음으로 표시"""
        data = self._load_data()
        topic_key = self._normalize_topic_name(topic_name)

        if topic_key not in data["topics"]:
            logger.error(f"❌ 주제를 찾을 수 없음: {topic_name}")
            return

        topic = data["topics"][topic_key]
        category_key = f"{category}_papers"

        # 논문 찾아서 status 업데이트
        for paper in topic.get(category_key, []):
            if paper["id"] == paper_id:
                paper["status"] = "read"

                # 읽은 논문 수 업데이트
                count_key = f"{category}_papers_read"
                topic["knowledge_state"][count_key] = topic["knowledge_state"].get(count_key, 0) + 1

                # 진행률 계산
                self._update_progress(topic)

                self._save_data(data)
                logger.info(f"✅ 논문 읽음 표시: {paper_id}")
                break

    def _update_progress(self, topic: Dict):
        """진행률 계산"""
        state = topic["knowledge_state"]
        total_papers = (
            len(topic.get("foundation_papers", [])) +
            len(topic.get("core_papers", [])) +
            len(topic.get("recent_papers", []))
        )

        if total_papers == 0:
            state["progress_percentage"] = 0.0
            return

        read_papers = (
            state.get("foundation_papers_read", 0) +
            state.get("core_papers_read", 0) +
            state.get("recent_papers_read", 0)
        )

        state["progress_percentage"] = round((read_papers / total_papers) * 100, 2)

        # 상태 자동 전환
        if state["progress_percentage"] >= 80:
            if state["state"] == "beginner":
                state["state"] = "intermediate"
                logger.info("🎉 상태 전환: beginner → intermediate")
            elif state["state"] == "intermediate":
                state["state"] = "experienced"
                logger.info("🎉 상태 전환: intermediate → experienced")

    def get_unread_papers(self, topic_name: str) -> Dict[str, List[Dict]]:
        """읽지 않은 논문 조회"""
        topic = self.get_topic_knowledge(topic_name)
        if not topic:
            return {"foundation": [], "core": [], "recent": []}

        result = {}
        for category in ["foundation", "core", "recent"]:
            papers = topic.get(f"{category}_papers", [])
            unread = [p for p in papers if p.get("status") != "read"]
            result[category] = unread

        return result

    def _normalize_topic_name(self, topic_name: str) -> str:
        """주제명 정규화 (소문자, 공백 제거)"""
        return topic_name.lower().replace(" ", "_")

    def get_all_topics(self) -> List[str]:
        """모든 주제 목록 조회"""
        data = self._load_data()
        return list(data["topics"].keys())

    def add_search_history(self, topic_name: str, search_info: Dict):
        """검색 이력 추가"""
        data = self._load_data()
        topic_key = self._normalize_topic_name(topic_name)

        if topic_key not in data["topics"]:
            self.create_topic(topic_name)
            data = self._load_data()

        topic = data["topics"][topic_key]
        if "search_history" not in topic:
            topic["search_history"] = []

        search_record = {
            "searched_at": datetime.now().isoformat(),
            **search_info
        }

        topic["search_history"].append(search_record)
        self._save_data(data)
        logger.info(f"📝 검색 이력 저장: {topic_name}")

