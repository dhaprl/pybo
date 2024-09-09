from django.contrib import admin
from pybo.models import Question

# =============================
# QuestionAdmin (관리자 설정)
# =============================
class QuestionAdmin(admin.ModelAdmin):
    # 관리자 페이지에서 검색 기능을 제공하기 위한 설정
    # 'subject' 필드 기준으로 검색 가능
    search_fields = ['subject']

# Question 모델을 관리자(admin) 페이지에 등록하고,
# QuestionAdmin 설정을 함께 적용하여 검색 기능 등 추가적인 설정이 반영되도록 함
admin.site.register(Question, QuestionAdmin)
