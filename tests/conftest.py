"""pytest 설정 및 공통 fixture"""

import sys
from pathlib import Path

import pytest

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_query():
    """샘플 쿼리"""
    return "청량리 아파트 시세가 얼마인가요?"


@pytest.fixture
def comparison_query():
    """비교 쿼리"""
    return "청량리와 이문동 중 어디가 더 오를까요?"


@pytest.fixture
def news_query():
    """뉴스 분석 쿼리"""
    return "GTX-C 개통이 청량리 시세에 어떤 영향을 줄까요?"
