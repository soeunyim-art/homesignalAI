"""뉴스 키워드 추출기 (config/keywords.yaml 연동)"""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# 프로젝트 루트 기준 키워드 설정 파일 경로
DEFAULT_KEYWORDS_PATH = Path(__file__).parent.parent.parent / "config" / "keywords.yaml"


class KeywordExtractor:
    """뉴스 키워드 추출기

    config/keywords.yaml에서 키워드를 로드하여
    뉴스 제목/본문에서 관련 키워드를 추출합니다.
    """

    def __init__(
        self,
        keywords_path: Path | str | None = None,
        custom_keywords: list[str] | None = None,
    ):
        """
        Args:
            keywords_path: keywords.yaml 파일 경로 (None이면 기본 경로)
            custom_keywords: 추가 커스텀 키워드
        """
        self._keywords_path = Path(keywords_path) if keywords_path else DEFAULT_KEYWORDS_PATH
        self._keywords: set[str] = set()
        self._categories: dict[str, list[str]] = {}

        self._load_keywords()

        if custom_keywords:
            self._keywords.update(custom_keywords)

    def _load_keywords(self) -> None:
        """keywords.yaml에서 키워드 로드"""
        if not self._keywords_path.exists():
            logger.warning(f"Keywords file not found: {self._keywords_path}")
            self._load_fallback_keywords()
            return

        try:
            with open(self._keywords_path, encoding="utf-8") as f:
                data: dict[str, Any] = yaml.safe_load(f)

            categories = data.get("categories", {})

            for category_name, category_data in categories.items():
                primary = category_data.get("primary", [])
                synonyms = category_data.get("synonyms", [])

                all_keywords = primary + synonyms
                self._categories[category_name] = all_keywords
                self._keywords.update(all_keywords)

            logger.info(
                f"Loaded {len(self._keywords)} keywords from {len(self._categories)} categories"
            )

        except Exception as e:
            logger.error(f"Failed to load keywords: {e}")
            self._load_fallback_keywords()

    def _load_fallback_keywords(self) -> None:
        """폴백 키워드 (파일 로드 실패 시)"""
        fallback = {
            "transport": ["GTX", "GTX-C", "청량리역", "지하철"],
            "redevelopment": ["재개발", "뉴타운", "이문휘경뉴타운", "재건축"],
            "supply": ["분양", "입주", "착공", "청약"],
            "policy": ["금리", "대출", "규제", "정책"],
        }
        for category, keywords in fallback.items():
            self._categories[category] = keywords
            self._keywords.update(keywords)

        logger.warning(f"Using fallback keywords: {len(self._keywords)} keywords")

    def extract(
        self,
        title: str,
        content: str | None = None,
    ) -> list[str]:
        """타겟 키워드 추출

        Args:
            title: 뉴스 제목
            content: 뉴스 본문 (선택)

        Returns:
            발견된 키워드 목록 (중복 제거)
        """
        text = title
        if content:
            text += " " + content

        text_upper = text.upper()
        found = []

        for keyword in self._keywords:
            if keyword.upper() in text_upper:
                found.append(keyword)

        return found

    def extract_by_category(
        self,
        title: str,
        content: str | None = None,
    ) -> dict[str, list[str]]:
        """카테고리별 키워드 추출

        Returns:
            카테고리: [발견된 키워드] 딕셔너리
        """
        text = title
        if content:
            text += " " + content

        text_upper = text.upper()
        result: dict[str, list[str]] = {}

        for category, keywords in self._categories.items():
            found = [kw for kw in keywords if kw.upper() in text_upper]
            if found:
                result[category] = found

        return result

    def extract_with_frequency(
        self,
        title: str,
        content: str | None = None,
    ) -> dict[str, int]:
        """키워드별 빈도 추출

        Returns:
            키워드: 등장 횟수 딕셔너리
        """
        text = title
        if content:
            text += " " + content

        text_upper = text.upper()
        freq: dict[str, int] = {}

        for keyword in self._keywords:
            count = text_upper.count(keyword.upper())
            if count > 0:
                freq[keyword] = count

        return freq

    def is_relevant(
        self,
        title: str,
        content: str | None = None,
        min_keywords: int = 1,
    ) -> bool:
        """뉴스가 관련성 있는지 판단

        Args:
            title: 뉴스 제목
            content: 뉴스 본문
            min_keywords: 최소 필요 키워드 수

        Returns:
            관련성 여부
        """
        keywords = self.extract(title, content)
        return len(keywords) >= min_keywords

    @property
    def all_keywords(self) -> set[str]:
        """전체 키워드 집합"""
        return self._keywords.copy()

    @property
    def categories(self) -> dict[str, list[str]]:
        """카테고리별 키워드"""
        return self._categories.copy()
