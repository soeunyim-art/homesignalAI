"""NLP 기반 키워드 추출기

형태소 분석을 통한 명사/동사 추출 및 키워드 식별
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class NLPKeywordExtractor:
    """NLP 기반 키워드 추출기
    
    KoNLPy/Mecab을 사용한 형태소 분석으로
    사용자 질문에서 핵심 키워드를 추출합니다.
    """

    # 한국어 불용어 (조사, 어미 등)
    STOPWORDS = {
        "은", "는", "이", "가", "을", "를", "의", "에", "에서", "로", "으로",
        "과", "와", "도", "만", "까지", "부터", "께서", "한테", "에게",
        "하다", "되다", "있다", "없다", "이다", "아니다",
        "그", "저", "이", "것", "수", "등", "및", "또", "또한",
        "어디", "언제", "어떻게", "왜", "무엇", "누구",
        "요", "네", "예", "아니오",
    }

    # 부동산 관련 중요 동사 (명사화)
    IMPORTANT_VERBS = {
        "오르다": "상승",
        "내리다": "하락",
        "떨어지다": "하락",
        "뛰다": "급등",
        "급등하다": "급등",
        "급락하다": "급락",
        "안정되다": "안정",
        "개발하다": "개발",
        "재개발하다": "재개발",
        "분양하다": "분양",
    }

    def __init__(self, use_mecab: bool = True):
        """
        Args:
            use_mecab: Mecab 사용 여부 (False면 간단한 규칙 기반)
        """
        self.use_mecab = use_mecab
        self.mecab = None
        
        if use_mecab:
            try:
                from konlpy.tag import Mecab
                self.mecab = Mecab()
                logger.info("Mecab 형태소 분석기 로드 완료")
            except ImportError:
                logger.warning(
                    "konlpy 또는 mecab-python3이 설치되지 않았습니다. "
                    "규칙 기반 추출로 대체합니다. "
                    "설치: uv sync --extra nlp"
                )
                self.use_mecab = False
            except Exception as e:
                logger.warning(f"Mecab 로드 실패: {e}. 규칙 기반 추출로 대체합니다.")
                self.use_mecab = False

    def extract_nouns(self, text: str) -> list[str]:
        """명사 추출
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            추출된 명사 목록 (불용어 제거, 2글자 이상)
        """
        if self.use_mecab and self.mecab:
            return self._extract_nouns_mecab(text)
        else:
            return self._extract_nouns_simple(text)

    def _extract_nouns_mecab(self, text: str) -> list[str]:
        """Mecab을 사용한 명사 추출"""
        try:
            nouns = self.mecab.nouns(text)  # type: ignore
            # 불용어 제거 및 2글자 이상 필터링
            filtered = [
                n for n in nouns 
                if n not in self.STOPWORDS and len(n) >= 2
            ]
            return filtered
        except Exception as e:
            logger.error(f"Mecab 명사 추출 실패: {e}")
            return self._extract_nouns_simple(text)

    def _extract_nouns_simple(self, text: str) -> list[str]:
        """간단한 규칙 기반 명사 추출 (Mecab 없을 때)
        
        완벽하지 않지만 기본적인 명사 패턴 추출
        """
        import re
        
        # 한글 2글자 이상 단어 추출
        words = re.findall(r'[가-힣]{2,}', text)
        
        # 불용어 및 조사 제거
        filtered = [
            w for w in words 
            if w not in self.STOPWORDS 
            and not self._is_josa(w)
        ]
        
        return list(set(filtered))

    def _is_josa(self, word: str) -> bool:
        """조사 여부 판단 (간단한 휴리스틱)"""
        josa_endings = ["은", "는", "이", "가", "을", "를", "에", "로", "와", "과"]
        return word in josa_endings

    def extract_with_pos(self, text: str) -> list[tuple[str, str]]:
        """품사 태깅
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            (단어, 품사) 튜플 리스트
        """
        if not self.use_mecab or not self.mecab:
            logger.warning("Mecab이 없어 품사 태깅을 수행할 수 없습니다.")
            return []
        
        try:
            return self.mecab.pos(text)  # type: ignore
        except Exception as e:
            logger.error(f"품사 태깅 실패: {e}")
            return []

    def extract_verbs(self, text: str) -> list[str]:
        """동사 추출 및 명사화
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            명사화된 동사 목록
        """
        if not self.use_mecab or not self.mecab:
            return []
        
        try:
            pos_tags = self.mecab.pos(text)  # type: ignore
            verbs = []
            
            for word, pos in pos_tags:
                # 동사 (VV, VA)
                if pos.startswith('V'):
                    # 중요 동사면 명사화
                    if word in self.IMPORTANT_VERBS:
                        verbs.append(self.IMPORTANT_VERBS[word])
                    elif len(word) >= 2:
                        verbs.append(word)
            
            return verbs
        except Exception as e:
            logger.error(f"동사 추출 실패: {e}")
            return []

    def extract_keywords(
        self, 
        text: str, 
        include_verbs: bool = True,
        min_length: int = 2,
    ) -> list[str]:
        """종합 키워드 추출
        
        명사 + (선택적) 동사를 추출하여 키워드 목록 반환
        
        Args:
            text: 분석할 텍스트
            include_verbs: 동사 포함 여부
            min_length: 최소 키워드 길이
            
        Returns:
            추출된 키워드 목록 (중복 제거)
        """
        keywords = []
        
        # 명사 추출
        nouns = self.extract_nouns(text)
        keywords.extend(nouns)
        
        # 동사 추출 (선택)
        if include_verbs:
            verbs = self.extract_verbs(text)
            keywords.extend(verbs)
        
        # 길이 필터링 및 중복 제거
        filtered = [k for k in keywords if len(k) >= min_length]
        return list(set(filtered))

    def extract_with_frequency(self, text: str) -> dict[str, int]:
        """키워드 빈도 추출
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            {키워드: 빈도} 딕셔너리
        """
        keywords = self.extract_keywords(text)
        freq: dict[str, int] = {}
        
        text_lower = text.lower()
        for keyword in keywords:
            count = text_lower.count(keyword.lower())
            if count > 0:
                freq[keyword] = count
        
        return freq

    def is_available(self) -> bool:
        """NLP 추출기 사용 가능 여부"""
        return self.use_mecab and self.mecab is not None
