"""
키워드 설정 로더

config/keywords.yaml 파일을 로드하고 키워드 관련 유틸리티 제공
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class KeywordCategory:
    """키워드 카테고리"""

    name: str
    primary: list[str]
    synonyms: list[str]

    def all_keywords(self) -> list[str]:
        """primary + synonyms 전체 키워드 반환"""
        return self.primary + self.synonyms


class KeywordConfig:
    """키워드 설정 관리"""

    def __init__(self, config_path: str | Path | None = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "keywords.yaml"
        
        self.config_path = Path(config_path)
        self._config: dict[str, Any] = {}
        self._categories: dict[str, KeywordCategory] = {}
        self._load()

    def _load(self):
        """설정 파일 로드"""
        if not self.config_path.exists():
            logger.warning(f"키워드 설정 파일이 없습니다: {self.config_path}")
            self._use_defaults()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
            
            categories_data = self._config.get("categories", {})
            for name, data in categories_data.items():
                self._categories[name] = KeywordCategory(
                    name=name,
                    primary=data.get("primary", []),
                    synonyms=data.get("synonyms", []),
                )
            
            logger.info(f"키워드 설정 로드 완료: {len(self._categories)}개 카테고리")
        
        except Exception as e:
            logger.error(f"키워드 설정 로드 실패: {e}")
            self._use_defaults()

    def _use_defaults(self):
        """기본 키워드 설정 사용"""
        self._categories = {
            "transport": KeywordCategory(
                name="transport",
                primary=["GTX", "GTX-C", "청량리역"],
                synonyms=["수도권광역급행철도", "환승센터"],
            ),
            "redevelopment": KeywordCategory(
                name="redevelopment",
                primary=["재개발", "뉴타운", "이문휘경뉴타운"],
                synonyms=["정비사업", "재건축", "리모델링"],
            ),
            "supply": KeywordCategory(
                name="supply",
                primary=["분양", "입주", "착공", "준공"],
                synonyms=["조합원", "특별공급", "청약"],
            ),
            "policy": KeywordCategory(
                name="policy",
                primary=["금리", "대출", "규제", "정책"],
                synonyms=["기준금리", "DSR", "LTV"],
            ),
        }

    def get_category(self, name: str) -> KeywordCategory | None:
        """카테고리 조회"""
        return self._categories.get(name)

    def get_all_categories(self) -> dict[str, KeywordCategory]:
        """전체 카테고리 반환"""
        return self._categories

    def get_primary_keywords(self, category: str | None = None) -> list[str]:
        """primary 키워드 목록 반환
        
        Args:
            category: 특정 카테고리만 조회 (None이면 전체)
        """
        if category:
            cat = self._categories.get(category)
            return cat.primary if cat else []
        
        keywords = []
        for cat in self._categories.values():
            keywords.extend(cat.primary)
        return keywords

    def get_all_keywords(self, category: str | None = None) -> list[str]:
        """primary + synonyms 전체 키워드 반환
        
        Args:
            category: 특정 카테고리만 조회 (None이면 전체)
        """
        if category:
            cat = self._categories.get(category)
            return cat.all_keywords() if cat else []
        
        keywords = []
        for cat in self._categories.values():
            keywords.extend(cat.all_keywords())
        return keywords

    def get_feature_mapping(self) -> dict[str, list[str]]:
        """피처 변수 매핑 반환
        
        Returns:
            {feature_name: [category_names]}
        """
        return self._config.get("feature_mapping", {})

    def get_keywords_for_feature(self, feature_name: str) -> list[str]:
        """특정 피처 변수에 해당하는 키워드 반환
        
        Args:
            feature_name: 피처 변수명 (예: news_freq_gtx)
        
        Returns:
            해당 피처에 매핑된 카테고리들의 전체 키워드
        """
        mapping = self.get_feature_mapping()
        categories = mapping.get(feature_name, [])
        
        keywords = []
        for cat_name in categories:
            keywords.extend(self.get_all_keywords(cat_name))
        
        return keywords


# 싱글톤 인스턴스
_keyword_config: KeywordConfig | None = None


def get_keyword_config() -> KeywordConfig:
    """키워드 설정 싱글톤 인스턴스 반환"""
    global _keyword_config
    if _keyword_config is None:
        _keyword_config = KeywordConfig()
    return _keyword_config
