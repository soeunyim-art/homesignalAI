"""
Ingest API Pydantic 스키마 정의

개발1(국토교통부 데이터), 개발2(뉴스 데이터) 적재를 위한 요청/응답 스키마
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


# =============================================================================
# Houses Data Schemas (개발1 - 국토교통부 API)
# =============================================================================


class HouseDataItem(BaseModel):
    """개별 부동산 거래 레코드"""

    complex_name: str = Field(..., description="아파트 단지명")
    dong_name: str | None = Field(None, description="법정동 (동대문구 세부 동)")
    price: float = Field(..., description="실거래가 (원)")
    bedrooms: float | None = Field(None, description="침실 수")
    bathrooms: float | None = Field(None, description="욕실 수")
    sqft_living: int | None = Field(None, description="전용면적 (제곱미터)")
    sqft_lot: int | None = Field(None, description="대지면적 (제곱미터)")
    floors: float | None = Field(None, description="층수")
    waterfront: int | None = Field(None, ge=0, le=1, description="수변 조망 여부")
    view: int | None = Field(None, ge=0, description="조망권 등급")
    condition: int | None = Field(None, ge=0, description="건물 상태")
    sqft_above: int | None = Field(None, description="지상층 면적")
    sqft_basement: int | None = Field(None, description="지하층 면적")
    yr_built: int | None = Field(None, ge=1900, le=2100, description="준공 연도")
    yr_renovated: int | None = Field(None, description="리모델링 연도")
    contract_date: datetime = Field(..., description="계약일")


class HouseDataBatchRequest(BaseModel):
    """부동산 데이터 배치 적재 요청"""

    source: str = Field(
        default="molit_api",
        description="데이터 소스 (molit_api, manual 등)",
    )
    items: list[HouseDataItem] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="거래 데이터 목록 (최대 1000건)",
    )


class HouseDataBatchResponse(BaseModel):
    """부동산 데이터 배치 적재 응답"""

    success: bool
    inserted_count: int = Field(..., description="성공적으로 적재된 건수")
    failed_count: int = Field(default=0, description="실패한 건수")
    errors: list[str] | None = Field(None, description="에러 메시지 목록")
    batch_id: str = Field(..., description="배치 추적용 고유 ID")


class HouseDataStatusResponse(BaseModel):
    """부동산 데이터 현황 응답"""

    total_records: int = Field(..., description="총 레코드 수")
    latest_contract_date: date | None = Field(None, description="최근 계약일")
    oldest_contract_date: date | None = Field(None, description="가장 오래된 계약일")
    dong_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="동별 레코드 분포",
    )
    last_ingestion_at: datetime | None = Field(None, description="마지막 적재 시각")


# =============================================================================
# News Signals Schemas (개발2 - 뉴스 크롤링)
# =============================================================================


class NewsSignalItem(BaseModel):
    """개별 뉴스 신호 레코드"""

    title: str = Field(..., min_length=1, max_length=500, description="뉴스 제목")
    content: str | None = Field(None, description="뉴스 본문 또는 요약")
    url: str | None = Field(None, description="원문 URL")
    keywords: list[str] = Field(
        default_factory=list,
        description="추출된 키워드 (GTX, 재개발 등)",
    )
    embedding: list[float] | None = Field(
        None,
        description="OpenAI text-embedding-3-small 벡터 (1536차원)",
    )
    published_at: datetime = Field(..., description="발행일시")


class NewsSignalBatchRequest(BaseModel):
    """뉴스 데이터 배치 적재 요청"""

    source: str = Field(
        default="google_news",
        description="데이터 소스 (google_news, naver_news, rss 등)",
    )
    items: list[NewsSignalItem] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="뉴스 데이터 목록 (최대 500건)",
    )
    generate_embeddings: bool = Field(
        default=True,
        description="embedding 미제공 시 백엔드에서 자동 생성 여부",
    )


class NewsSignalBatchResponse(BaseModel):
    """뉴스 데이터 배치 적재 응답"""

    success: bool
    inserted_count: int = Field(..., description="성공적으로 적재된 건수")
    duplicate_count: int = Field(default=0, description="중복(URL 기준) 건수")
    embedding_generated_count: int = Field(
        default=0,
        description="임베딩 자동 생성된 건수",
    )
    failed_count: int = Field(default=0, description="실패한 건수")
    errors: list[str] | None = Field(None, description="에러 메시지 목록")
    batch_id: str = Field(..., description="배치 추적용 고유 ID")


class NewsSignalStatusResponse(BaseModel):
    """뉴스 데이터 현황 응답"""

    total_records: int = Field(..., description="총 레코드 수")
    with_embedding_count: int = Field(..., description="임베딩 보유 레코드 수")
    keyword_frequency: dict[str, int] = Field(
        default_factory=dict,
        description="키워드별 빈도",
    )
    latest_published_at: datetime | None = Field(None, description="최근 발행일시")
    last_ingestion_at: datetime | None = Field(None, description="마지막 적재 시각")


# =============================================================================
# Predictions Schemas (백엔드 내부용)
# =============================================================================


class PredictionItem(BaseModel):
    """개별 예측 결과 레코드"""

    model_version: str = Field(..., description="모델 버전 (예: v1.0-prophet-lgbm)")
    target_date: date = Field(..., description="예측 대상 일자")
    predicted_price: float = Field(..., description="예측 가격")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="신뢰도")
    features_used: dict | None = Field(
        None,
        description="예측에 사용된 피처 및 가중치",
    )


class PredictionBatchRequest(BaseModel):
    """예측 결과 배치 저장 요청"""

    items: list[PredictionItem] = Field(
        ...,
        min_length=1,
        description="예측 결과 목록",
    )


class PredictionBatchResponse(BaseModel):
    """예측 결과 배치 저장 응답"""

    success: bool
    inserted_count: int
    batch_id: str


# =============================================================================
# Auth Schemas
# =============================================================================


class UserRole(BaseModel):
    """사용자 역할 정보"""

    user_id: str
    role: Literal["data_collector_molit", "data_collector_news", "service_account"]
    email: str | None = None
