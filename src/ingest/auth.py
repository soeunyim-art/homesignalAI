"""
Ingest API 인증 모듈 - Supabase Auth JWT 검증

Supabase Auth의 JWT 토큰을 검증하고 역할(Role) 기반 접근 제어 수행
"""

import logging
from typing import Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import settings
from src.shared.database import get_supabase_client

from .schemas import UserRole

logger = logging.getLogger(__name__)

# Bearer 토큰 스킴
security = HTTPBearer(auto_error=False)

# 역할 타입 정의
RoleType = Literal["data_collector_molit", "data_collector_news", "service_account"]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> UserRole:
    """
    Supabase Auth JWT 토큰 검증 및 사용자 정보 추출

    개발 모드(debug=True)에서는 인증 없이 service_account 역할 반환
    """
    # 개발 모드에서는 인증 스킵
    if settings.debug and credentials is None:
        logger.warning("개발 모드: 인증 없이 service_account 역할로 진행")
        return UserRole(
            user_id="dev-user",
            role="service_account",
            email="dev@localhost",
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Supabase 클라이언트로 토큰 검증
        supabase = get_supabase_client()
        user_response = supabase.auth.get_user(token)

        if user_response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다",
            )

        user = user_response.user
        user_metadata = user.user_metadata or {}

        # 역할 추출 (기본값: service_account)
        role = user_metadata.get("role", "service_account")

        # 유효한 역할인지 확인
        valid_roles = [
            settings.ingest_role_molit,
            settings.ingest_role_news,
            settings.ingest_role_internal,
        ]
        if role not in valid_roles:
            logger.warning(f"알 수 없는 역할: {role}, service_account로 대체")
            role = "service_account"

        return UserRole(
            user_id=user.id,
            role=role,
            email=user.email,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"토큰 검증 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰 검증에 실패했습니다",
        )


def require_role(allowed_roles: list[RoleType]):
    """
    특정 역할만 접근 허용하는 의존성 생성

    사용 예:
        @router.post("/houses")
        async def ingest_houses(
            user: UserRole = Depends(require_role(["data_collector_molit"]))
        ):
            ...
    """

    async def role_checker(
        user: UserRole = Depends(get_current_user),
    ) -> UserRole:
        if user.role not in allowed_roles:
            logger.warning(
                f"권한 부족: user={user.user_id}, role={user.role}, "
                f"required={allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"이 작업에는 {allowed_roles} 역할이 필요합니다",
            )
        return user

    return role_checker


# 편의를 위한 사전 정의된 의존성
require_molit_role = require_role(["data_collector_molit", "service_account"])
require_news_role = require_role(["data_collector_news", "service_account"])
require_internal_role = require_role(["service_account"])
require_any_ingest_role = require_role([
    "data_collector_molit",
    "data_collector_news",
    "service_account",
])
