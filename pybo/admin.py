# 모델을 등록해서 사용하세요
#
from django.contrib import admin
from .models import Question
#
#관리자가 질문을 검색 할 수 있도록 검색 항목 추가
class QuestionAdmin(admin.ModelAdmin):
    search_fields = ['subject']
#
#질문 모델을 관리자 권한으로 사이트에서 관리할 수 있음(pybo에 있는것은 pybo에서 실행되는 것이기때문에)
# admin.site.register(Question)
#관리자가 질문에 접근하고 제목으로 검색 할 수 있음
admin.site.register(Question,QuestionAdmin)
