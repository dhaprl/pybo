from django.core.paginator import Paginator  # 페이징 처리를 위한 Paginator 클래스
from django.shortcuts import render, get_object_or_404  # 뷰 처리, 객체 조회 기능
from django.db.models import Q  # 검색 조건을 위한 Q 객체
import logging  # 로그 출력을 위한 모듈

logger = logging.getLogger('pybo')  # 'pybo'라는 로거 생성

from ..models import Question  # Question 모델 가져오기

# =======================================
# pybo 질문 목록 출력 뷰
# =======================================
def index(request):
    ''' pybo 목록 출력 '''
    # INFO 레벨 로그 메시지 출력
    logger.info("INFO 레벨로 출력")

    # ===============================
    # 입력 인자 처리
    # ===============================

    # GET 요청에서 'page' 번호를 가져옵니다. 없으면 기본값으로 '1'을 사용
    page = request.GET.get('page', '1')  
    
    # GET 요청에서 'kw' (검색어)를 가져옵니다. 없으면 기본값으로 빈 문자열을 사용
    kw = request.GET.get('kw', '')  
    
    # ===============================
    # 데이터 조회
    # ===============================

    # Question 모델의 데이터를 최신순으로 정렬하여 가져옵니다.
    question_list = Question.objects.order_by('-create_date')  
    
    # 검색어(kw)가 있으면 필터링 수행
    if kw:
        # 제목, 내용, 답변 내용, 질문 글쓴이, 답변 글쓴이에서 검색어를 포함한 데이터 필터링
        question_list = question_list.filter(
            Q(subject__icontains=kw) |  # 제목에 검색어 포함
            Q(content__icontains=kw) |  # 내용에 검색어 포함
            Q(answer__content__icontains=kw) |  # 답변 내용에 검색어 포함
            Q(author__username__icontains=kw) |  # 질문 글쓴이 이름에 검색어 포함
            Q(answer__author__username__icontains=kw)  # 답변 글쓴이 이름에 검색어 포함
        ).distinct()  # 중복 제거

    # ===============================
    # 페이징 처리
    # ===============================

    # 페이지네이터(Paginator)를 사용해 한 페이지에 10개 항목씩 표시
    paginator = Paginator(question_list, 10)  
    
    # 현재 페이지 번호에 해당하는 데이터 가져오기
    page_obj = paginator.get_page(page)  
    
    # ===============================
    # 템플릿에 전달할 데이터 설정
    # ===============================

    # 템플릿에 전달할 데이터 정의 (페이지 객체, 현재 페이지 번호, 검색어)
    context = {'QList': page_obj, 'page': page, 'kw': kw}  
    
    # 템플릿 'pybo/question_list.html'을 렌더링하여 응답 반환
    return render(request, 'pybo/question_list.html', context)  

# =======================================
# pybo 질문 상세 내용 출력 뷰
# =======================================
def detail(request, question_id):
    ''' pybo 내용 출력 '''

    # 주어진 question_id에 해당하는 Question 객체를 가져옵니다. 없으면 404 에러 발생
    question = get_object_or_404(Question, pk=question_id)  
    
    # 질문에 달린 댓글들 중, 부모가 없는 댓글들(최상위 댓글)을 가져옵니다.
    comments = question.comments.filter(parent__isnull=True)
    
    # 템플릿에 전달할 데이터 설정 (질문, 댓글)
    context = {'question': question, 'comments': comments}  
    
    # 템플릿 'pybo/question_detail.html'을 렌더링하여 응답 반환
    return render(request, 'pybo/question_detail.html', context)  

#########################################
# 제네릭 뷰를 사용한 방법 (주석 처리)
#########################################
# # 클래스 기반의 제네릭 뷰를 사용하여 질문 목록 및 상세 내용을 처리할 수 있음
# from django.views import generic

# # pybo 질문 목록을 출력하는 클래스 기반 뷰 (ListView)
# class IndexView(generic.ListView): 
#     """
#     pybo 목록 출력
#     """
#     # 기본적으로 모델명_list.html 템플릿을 사용
#     model = Question  # 모델 설정

#     # 최신 순으로 정렬된 질문 목록을 반환
#     def get_queryset(self):
#         return Question.objects.order_by('-create_date')

# # pybo 질문 상세 내용을 출력하는 클래스 기반 뷰 (DetailView)
# class DetailView(generic.DetailView):
#     """
#     pybo 내용 출력
#     """
#     model = Question  # Question 모델을 사용하여 상세 내용을 출력
