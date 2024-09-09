import markdown  # 마크다운 문자열을 HTML로 변환하기 위한 모듈
from django import template  # Django 템플릿 라이브러리
from django.utils.safestring import mark_safe  # 안전한 HTML 문자열로 변환하는 함수

# ===============================
# 템플릿 라이브러리 객체 생성
# ===============================
# 템플릿 필터를 등록하기 위한 Library 객체 생성
register = template.Library()

# ===============================
# 커스텀 필터: 뺄셈 연산을 수행하는 필터
# ===============================
@register.filter  # Django 템플릿 필터로 등록
def sub(value, arg):
    """
    'sub' 필터는 value에서 arg를 뺀 결과를 반환합니다.
    템플릿에서 사용 시:
    {{ value|sub:arg }} 형태로 사용되어 value - arg 결과를 출력합니다.
    """
    return value - arg

# ===============================
# 커스텀 필터: 마크다운 문자열을 HTML로 변환
# ===============================
@register.filter  # Django 템플릿 필터로 등록
def mark(value):
    """
    'mark' 필터는 마크다운 문자열을 HTML로 변환하고 안전한 문자열로 처리합니다.
    
    마크다운 확장 기능으로 'nl2br'과 'fenced_code'를 사용합니다.
    - 'nl2br': 줄바꿈 문자를 <br> 태그로 변환
    - 'fenced_code': 코드 블록을 마크다운 형식으로 처리
    
    사용 예:
    {{ value|mark }} 형태로 템플릿에서 사용하여 마크다운을 HTML로 변환합니다.
    
    Args:
        value (str): 변환할 마크다운 문자열
    
    Returns:
        str: HTML로 변환된 안전한 문자열
    """
    
    # value가 None인 경우 빈 문자열로 설정
    if value is None:
        value = ""
    
    # 마크다운 확장 기능 목록 설정
    extensions = ["nl2br", "fenced_code"]
    
    # 마크다운을 HTML로 변환하고, 안전한 HTML로 처리하여 반환
    return mark_safe(markdown.markdown(value, extensions=extensions))

"""
mark 함수는 markdown 모듈과 mark_safe 함수를 이용하여 입력 문자열을 HTML로 변환하는 필터 함수입니다. 

마크다운에는 몇 가지 확장 기능이 있는데 파이보는 위처럼 nl2br과 fenced_code를 사용하도록 설정했습니다. 

nl2br은 줄바꿈 문자를 <br> 로 바꾸어 줍니다. fenced_code는 위에서 살펴본 마크다운의 소스코드 표현을 위해 필요합니다.

nl2br을 사용하지 않을 경우 줄바꿈을 하기 위해서는 줄 끝에 스페이스(' ')를 두 개 연속으로 입력해야 합니다.

마크다운의 더 많은 확장 기능은 다음 문서를 참고하세요.

마크다운 확장 기능 문서: https://python-markdown.github.io/extensions/
"""
