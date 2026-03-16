"""pytest 설정 및 공통 fixture"""

import os
import sys
from pathlib import Path

import pytest

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """pytest 시작 전 환경변수 설정 (가장 빠른 시점)"""
    test_env_vars = {
        "SUPABASE_URL": "https://placeholder.supabase.co",
        "SUPABASE_KEY": "test-anon-key",
        "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key",
        "SUPABASE_TIMEOUT": "10",
        "OPENAI_API_KEY": "sk-test-openai-key",
        "ANTHROPIC_API_KEY": "sk-ant-test-anthropic-key",
        "AI_PROVIDER": "openai",
        "DEBUG": "true",
        "APP_ENV": "development",
        "REDIS_URL": "redis://localhost:6379/0",
    }

    for key, value in test_env_vars.items():
        if key not in os.environ:
            os.environ[key] = value


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """모든 테스트에 자동 적용되는 환경변수 설정"""
    # 환경변수 저장 (원래 값 백업)
    original_env = {}

    test_env_vars = {
        "SUPABASE_URL": "https://placeholder.supabase.co",
        "SUPABASE_KEY": "test-anon-key",
        "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key",
        "SUPABASE_TIMEOUT": "10",
        "OPENAI_API_KEY": "sk-test-openai-key",
        "ANTHROPIC_API_KEY": "sk-ant-test-anthropic-key",
        "AI_PROVIDER": "openai",
        "DEBUG": "true",
        "APP_ENV": "development",
        "REDIS_URL": "redis://localhost:6379/0",
    }

    # 환경변수 설정
    for key, value in test_env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # 테스트 종료 후 원래 환경변수 복원
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


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


@pytest.fixture
def mock_ai_client():
    """Mock AI Client for testing"""
    from unittest.mock import AsyncMock

    mock = AsyncMock()

    # Mock generate 메서드 (AIKeywordExtractor용)
    async def mock_generate(messages, temperature=0.7, max_tokens=1000, **kwargs):
        return '''```json
{
  "keywords": ["청량리", "재개발", "GTX"],
  "categories": ["redevelopment", "transport"],
  "intent": "forecast",
  "confidence": 0.9
}
```'''

    # Mock generate_completion 메서드
    async def mock_generate_completion(
        messages, system_prompt=None, temperature=0.7, max_tokens=1000
    ):
        return {
            "content": "테스트 응답입니다. 청량리 지역의 부동산 시세는 GTX-C 개통 등의 호재로 상승이 예상됩니다.",
            "model": "mock-model",
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }

    # Mock extract_json 메서드 (AI 키워드 추출용)
    async def mock_extract_json(prompt, schema=None):
        return {
            "keywords": ["GTX-C", "재개발", "청량리"],
            "confidence": 0.9,
            "categories": {"transport": ["GTX-C"], "redevelopment": ["재개발"]},
        }

    mock.generate = mock_generate
    mock.generate_completion = mock_generate_completion
    mock.extract_json = mock_extract_json

    return mock
