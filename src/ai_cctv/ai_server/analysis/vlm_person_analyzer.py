# AI CCTV 운영용 VLM 인물 분석기 진입 파일입니다.
# 기존 Qwen 기반 분석 구현을 테스트 파일명이 아닌 안정적인 모듈명으로 제공합니다.
# VLMWorker는 이 파일을 통해 인물 crop 이미지 분석 기능을 사용합니다.

from .qwen_person_analyzer import PersonAnalyzer as QwenPersonAnalyzer


class PersonAnalyzer(QwenPersonAnalyzer):
    """운영 코드에서 사용할 인물 이미지 VLM 분석기입니다.

    인자:
        model_id: HuggingFace 모델 식별자입니다.
        min_pixels: 입력 이미지 최소 픽셀 설정입니다.
        max_pixels: 입력 이미지 최대 픽셀 설정입니다.
        use_4bit: 4bit 양자화 사용 여부입니다.
    반환값:
        PersonAnalyzer 인스턴스를 반환합니다.
    """

    pass

