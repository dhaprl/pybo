from .ai_system import setup_django_system  # AI 시스템 설정을 위한 데코레이터 가져오기

# ===============================
# AI 처리 시작 함수
# ===============================
@setup_django_system  # setup_django_system 데코레이터를 적용하여 Django 환경 설정
def start_ai(request, image_path, face_recognition_system, target_encodings, selected_detectors, selected_predictors):
    """
    AI 얼굴 인식 시스템을 시작하는 함수입니다.
    
    이 함수는 이미지 경로를 받아 얼굴 인식 시스템을 이용하여 이미지를 처리하고,
    처리된 결과 이미지 경로를 반환합니다.
    
    Args:
        request: Django의 HTTP 요청 객체
        image_path (str): 처리할 이미지 파일의 경로
        face_recognition_system: 얼굴 인식 시스템 객체
        target_encodings: 얼굴 인식에 필요한 타겟 인코딩 정보
        selected_detectors: 사용자가 선택한 탐지기 목록
        selected_predictors: 사용자가 선택한 예측기 목록
    
    Returns:
        str: 처리된 이미지의 출력 경로
    """
    
    # 얼굴 인식 시스템을 사용하여 이미지를 처리하고, 결과 이미지의 경로를 받음
    output_path = face_recognition_system.process_image(image_path, target_encodings)
    
    # 처리된 이미지의 경로를 반환
    return output_path
    #
#
