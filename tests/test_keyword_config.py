"""
키워드 설정 로더 테스트
"""

import pytest

from src.shared.keyword_config import KeywordConfig, get_keyword_config


class TestKeywordConfig:
    """키워드 설정 테스트"""

    def test_load_config(self):
        """설정 파일 로드 테스트"""
        config = KeywordConfig()

        assert len(config.get_all_categories()) > 0

    def test_get_category(self):
        """카테고리 조회 테스트"""
        config = KeywordConfig()

        transport = config.get_category("transport")
        assert transport is not None
        assert "GTX" in transport.primary

        redevelopment = config.get_category("redevelopment")
        assert redevelopment is not None
        assert "재개발" in redevelopment.primary

    def test_get_primary_keywords(self):
        """primary 키워드 조회 테스트"""
        config = KeywordConfig()

        all_primary = config.get_primary_keywords()
        assert len(all_primary) > 0
        assert "GTX" in all_primary
        assert "재개발" in all_primary

        transport_primary = config.get_primary_keywords("transport")
        assert "GTX" in transport_primary
        assert "재개발" not in transport_primary

    def test_get_all_keywords(self):
        """전체 키워드 조회 테스트"""
        config = KeywordConfig()

        all_keywords = config.get_all_keywords()
        assert len(all_keywords) > 0
        assert "GTX" in all_keywords
        assert "수도권광역급행철도" in all_keywords

        transport_keywords = config.get_all_keywords("transport")
        assert "GTX" in transport_keywords
        assert "환승센터" in transport_keywords

    def test_get_feature_mapping(self):
        """피처 매핑 조회 테스트"""
        config = KeywordConfig()

        mapping = config.get_feature_mapping()
        assert "news_freq_gtx" in mapping
        assert "transport" in mapping["news_freq_gtx"]

    def test_get_keywords_for_feature(self):
        """피처별 키워드 조회 테스트"""
        config = KeywordConfig()

        gtx_keywords = config.get_keywords_for_feature("news_freq_gtx")
        assert len(gtx_keywords) > 0
        assert "GTX" in gtx_keywords

        redev_keywords = config.get_keywords_for_feature("news_freq_redev")
        assert len(redev_keywords) > 0
        assert "재개발" in redev_keywords

    def test_singleton(self):
        """싱글톤 인스턴스 테스트"""
        config1 = get_keyword_config()
        config2 = get_keyword_config()

        assert config1 is config2

    def test_default_fallback(self):
        """설정 파일 없을 때 기본값 사용 테스트"""
        config = KeywordConfig(config_path="/nonexistent/path.yaml")

        categories = config.get_all_categories()
        assert len(categories) > 0
        assert "transport" in categories
        assert "redevelopment" in categories
