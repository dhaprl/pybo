from django.urls import path
from .views import base_views, question_views, answer_views, comment_view

app_name = 'pybo'  # URL 네임스페이스. 다른 앱의 URL 패턴과 충돌하지 않도록 설정

"""
path 함수 설명:
1. 첫 번째 인수: URL 패턴을 나타냄.
2. 두 번째 인수: 해당 URL 패턴에 매핑되는 뷰 함수.
3. 세 번째 인수: URL 패턴에 대한 별칭 (템플릿에서 URL을 쉽게 참조하기 위해 사용).

예:
path('', base_views.index, name='index')는
기본 URL('/')에 해당하며, 이 URL로 접근할 때 base_views.index 함수를 호출하고
별칭 'index'로 템플릿 등에서 참조할 수 있음.
"""

urlpatterns = [
    ###########################################################################################################
    # base_views.py 관련 URL
    ###########################################################################################################

    # 메인 페이지 (질문 목록 페이지)로 이동. 기본 URL('/')에 매핑되며, base_views.index 함수가 호출됨.
    path('', base_views.index, name='index'),

    # 질문 상세 페이지로 이동. question_id 매개변수를 받아 해당 질문의 세부 내용을 보여주는 base_views.detail 함수 호출.
    path('<int:question_id>/', base_views.detail, name='detail'),
    
    ###########################################################################################################
    # question_views.py 관련 URL
    ###########################################################################################################

    # 질문 생성 페이지로 이동. question_views.question_create 함수가 호출되어 새로운 질문을 작성할 수 있는 페이지로 이동.
    path('question/create/', question_views.question_create, name='question_create'),
    
    # 질문 수정 페이지로 이동. question_id 매개변수를 받아 기존 질문을 수정할 수 있는 question_views.question_modify 함수 호출.
    path('question/modify/<int:question_id>/', question_views.question_modify, name='question_modify'),
    
    # 질문 삭제 처리. question_id를 받아 해당 질문을 삭제하는 question_views.question_delete 함수 호출.
    path('question/delete/<int:question_id>/', question_views.question_delete, name='question_delete'),
    
    # 질문 추천 처리. question_id를 받아 해당 질문에 추천을 추가하는 question_views.question_vote 함수 호출.
    path('question/vote/<int:question_id>/', question_views.question_vote, name='question_vote'),
    
    ###########################################################################################################
    # answer_views.py 관련 URL
    ###########################################################################################################

    # 답변 생성 페이지로 이동. question_id를 받아 해당 질문에 답변을 작성하는 answer_views.answer_create 함수 호출.
    path('answer/create/<int:question_id>/', answer_views.answer_create, name='answer_create'),
    
    # 답변 수정 페이지로 이동. answer_id를 받아 해당 답변을 수정할 수 있는 answer_views.answer_modify 함수 호출.
    path('answer/modify/<int:answer_id>/', answer_views.answer_modify, name='answer_modify'),
    
    # 답변 삭제 처리. answer_id를 받아 해당 답변을 삭제하는 answer_views.answer_delete 함수 호출.
    path('answer/delete/<int:answer_id>/', answer_views.answer_delete, name='answer_delete'),
    
    # 답변 추천 처리. answer_id를 받아 해당 답변에 추천을 추가하는 answer_views.answer_vote 함수 호출.
    path('answer/vote/<int:answer_id>/', answer_views.answer_vote, name='answer_vote'),
    
    ###########################################################################################################
    # comment_views.py 관련 URL
    ###########################################################################################################

    # 질문에 대한 댓글 생성. question_id를 받아 해당 질문에 댓글을 작성하는 comment_view.comment_create_question 함수 호출.
    path('comment/create/question/<int:question_id>/', comment_view.comment_create_question, name='comment_create_question'),
    
    # 질문에 대한 댓글 수정. comment_id를 받아 해당 댓글을 수정하는 comment_view.comment_modify_question 함수 호출.
    path('comment/modify/question/<int:comment_id>/', comment_view.comment_modify_question, name='comment_modify_question'),
    
    # 질문에 대한 댓글 삭제. comment_id를 받아 해당 댓글을 삭제하는 comment_view.comment_delete_question 함수 호출.
    path('comment/delete/question/<int:comment_id>/', comment_view.comment_delete_question, name='comment_delete_question'),
]
