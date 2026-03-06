"""키워드 추출기 테스트"""

import pytest

from src.crawler.keyword_extractor import KeywordExtractor


@pytest.fixture
def extractor() -> KeywordExtractor:
    """기본 키워드 추출기"""
    return KeywordExtractor()


def test_extract_gtx_keyword(extractor: KeywordExtractor):
    """GTX 키워드 추출 테스트"""
    keywords = extractor.extract("GTX-C 청량리역 2028년 개통")

    assert "GTX" in keywords or "GTX-C" in keywords
    assert "청량리역" in keywords


def test_extract_redevelopment_keywords(extractor: KeywordExtractor):
    """재개발 관련 키워드 추출 테스트"""
    keywords = extractor.extract("동대문구 재개발 사업 속도")

    assert "재개발" in keywords


def test_extract_newtown_keywords(extractor: KeywordExtractor):
    """뉴타운 관련 키워드 추출 테스트"""
    keywords = extractor.extract("이문휘경뉴타운 분양 일정 공개")

    assert "이문휘경뉴타운" in keywords or "뉴타운" in keywords


def test_extract_with_content(extractor: KeywordExtractor):
    """제목 + 본문에서 키워드 추출 테스트"""
    title = "청량리역 주변 개발"
    content = "GTX-C 노선 개통과 재개발 사업으로 부동산 시장이 활성화되고 있다."

    keywords = extractor.extract(title, content)

    assert "GTX" in keywords or "GTX-C" in keywords
    assert "재개발" in keywords
    assert "청량리역" in keywords


def test_extract_no_keywords(extractor: KeywordExtractor):
    """관련 키워드 없는 경우 테스트"""
    keywords = extractor.extract("오늘 날씨가 좋습니다")

    assert len(keywords) == 0


def test_extract_by_category(extractor: KeywordExtractor):
    """카테고리별 키워드 추출 테스트"""
    result = extractor.extract_by_category("GTX-C 청량리역 재개발 분양 금리")

    # 카테고리가 존재하는지 확인
    assert len(result) > 0

    # transport 카테고리에 GTX 관련 키워드
    if "transport" in result:
        assert any("GTX" in kw for kw in result["transport"])


def test_extract_with_frequency(extractor: KeywordExtractor):
    """키워드 빈도 추출 테스트"""
    freq = extractor.extract_with_frequency("GTX GTX GTX 재개발 재개발 청량리")

    assert freq.get("GTX", 0) == 3
    assert freq.get("재개발", 0) == 2


def test_is_relevant_true(extractor: KeywordExtractor):
    """관련성 판단 (관련 있음) 테스트"""
    assert extractor.is_relevant("GTX-C 청량리역 개통")


def test_is_relevant_false(extractor: KeywordExtractor):
    """관련성 판단 (관련 없음) 테스트"""
    assert not extractor.is_relevant("오늘의 날씨 예보")


def test_is_relevant_min_keywords(extractor: KeywordExtractor):
    """최소 키워드 수 기준 테스트"""
    # GTX만 있는 경우
    assert extractor.is_relevant("GTX 관련 뉴스", min_keywords=1)
    assert not extractor.is_relevant("GTX 관련 뉴스", min_keywords=2)

    # GTX, 청량리역 두 개 있는 경우
    assert extractor.is_relevant("GTX 청량리역 뉴스", min_keywords=2)


def test_custom_keywords():
    """커스텀 키워드 추가 테스트"""
    custom = ["테스트키워드", "임시키워드"]
    extractor = KeywordExtractor(custom_keywords=custom)

    keywords = extractor.extract("테스트키워드가 포함된 뉴스")

    assert "테스트키워드" in keywords


def test_all_keywords_property(extractor: KeywordExtractor):
    """전체 키워드 집합 반환 테스트"""
    all_keywords = extractor.all_keywords

    assert isinstance(all_keywords, set)
    assert len(all_keywords) > 0
    assert "GTX" in all_keywords or any("GTX" in kw for kw in all_keywords)


def test_categories_property(extractor: KeywordExtractor):
    """카테고리별 키워드 반환 테스트"""
    categories = extractor.categories

    assert isinstance(categories, dict)
    # config/keywords.yaml에 정의된 카테고리가 있는지 확인
    # (폴백 키워드도 포함)
    assert len(categories) > 0
