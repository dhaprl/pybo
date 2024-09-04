from django.shortcuts import render
from ..models import Question, Answer, Comment
# from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.shortcuts import redirect
from ..forms import QuestionForm, AnswerForm, CommentForm
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count

def index(request):

    """

    pybo 목록 출력

    """
    #입력 인자
    page = request.GET.get('page', '1') #페이지
    kw = request.GET.get('kw','') #검색어
    so = request.GET.get('so','recent')
    #log test
    0/3
    0/1
    1/0
    #
    #create_date 변수에 -를 붙여서 역순으로 정렬한다. (order_by)
    #조회(최근 순)
    if so == 'recommend':
        question_list = Question.objects.annotate(
            num_voter = Count('voter')).order_by('-num_voter','-create_date')
    elif so == 'popular':
        question_list = Question.objects.annotate(
            num_answer =Count('answer')).order_by('-num_answer','-create_date')
    else: #recent
        question_list = Question.objects.order_by('-create_date')
    #question_list = Question.objects.order_by('-create_date')
    if kw:
        question_list = question_list.filter(
            Q(subject__icontains=kw)|
            Q(content__icontains=kw)|
            Q(author__username__icontains=kw)|
            Q(answer__author__username__icontains=kw)).distinct()
    #만들어진 날짜순*오래된 순
    #question_list = Question.objects.order_by('create_date')

    #페이징 만들기
    paginator = Paginator(question_list, 10) #페이지당 10개씩 질문 목록 보여주기
    page_obj = paginator.get_page(page)

    #출력
    context = {'question_list' : page_obj,'page':page,'kw':kw, 'so':so}

    # context = {'question_list' : question_list}
    # return  HttpResponse("안녕하세요 pybo에 오신걸 환영합니다.")
    return render(request, 'pybo/question_list.html', context)

#질문을 눌렀을때 연결되는 url로직


def detail(request, question_id):
    """

    pybo 내용 출력

    """
    #question모델 객체의 아이디를 얻어와서  변수에 저장
    #하지만 존재하지 pybo/30과 같은 id숫자가 존재하지 않는 경우에 다른 출력 결과를 입력하기 위해
    # question = Question.objects.get(id=question_id)
    question = get_object_or_404(Question, pk = question_id)
    context = {'question' : question }
    return render(request, 'pybo/question_detail.html', context)