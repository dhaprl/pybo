from django.contrib import messages  # 사용자에게 메시지를 전달하는 모듈
from django.contrib.auth.decorators import login_required  # 로그인 필요를 확인하는 데코레이터
from django.shortcuts import render, get_object_or_404, redirect, resolve_url  # 뷰 처리, 객체 조회, 리다이렉트, URL 처리 기능
from django.utils import timezone  # 시간 처리를 위한 유틸리티 모듈

from ..forms import AnswerForm  # 답변 작성 폼
from ..models import Question, Answer  # Question과 Answer 모델

########################################################################################################

"""
로그아웃 상태에서는 request.user가 AnonymousUser 객체이므로 에러가 발생할 수 있음 
-> 로그인 상태에서만 답변을 작성할 수 있도록 로그인 필요 데코레이터 추가
"""
@login_required(login_url='common:login')  # 로그인 상태에서만 접근 가능하게 설정, 비로그인 사용자는 로그인 페이지로 리다이렉트
def answer_create(request, question_id):
    """ pybo 답변 등록 """
    
    # question_id에 해당하는 Question 객체를 가져오고, 없으면 404 에러 반환
    question = get_object_or_404(Question, pk=question_id)
    
    # POST 요청 시 답변 폼 데이터 처리
    if request.method == 'POST':
        form = AnswerForm(request.POST, request.FILES)  # 파일 업로드 처리 (request.FILES 추가)
        
        # 폼이 유효한 경우
        if form.is_valid():
            # commit=False로 일단 객체만 생성하고 DB에는 저장하지 않음
            answer = form.save(commit=False)
            answer.author = request.user  # 답변 작성자는 현재 로그인한 사용자
            answer.create_date = timezone.now()  # 답변 작성 시간 설정
            answer.question = question  # 답변이 달린 질문 설정
            answer.answer_image = None  # 기본적으로 이미지 없음 설정
            answer.save()  # 최종적으로 답변 DB에 저장
            
            # 답변 작성 후 질문 상세 페이지로 리다이렉트하고 앵커로 해당 답변 위치로 이동
            return redirect('{}#answer_{}'.format(resolve_url('pybo:detail', question_id=question.id), answer.id))
    
    # GET 요청 시 빈 폼 생성
    else:
        form = AnswerForm()
    
    # 템플릿에 전달할 데이터 설정
    context = {'question': question, 'form': form}
    
    # 'pybo/question_detail.html' 템플릿을 렌더링하여 응답 반환
    return render(request, 'pybo/question_detail.html', context)

########################################################################################################

@login_required(login_url='common:login')  # 로그인 상태에서만 접근 가능하게 설정
def answer_modify(request, answer_id):
    """ pybo 답변 수정 """
    
    # answer_id에 해당하는 Answer 객체를 가져오고, 없으면 404 에러 반환
    answer = get_object_or_404(Answer, pk=answer_id)
    
    # 현재 로그인한 사용자가 답변 작성자가 아닐 경우 에러 메시지를 출력
    if request.user != answer.author:
        messages.error(request, '수정권한이 없습니다')
        return redirect('pybo:detail', question_id=answer.question.id)  # 권한이 없으면 질문 상세 페이지로 리다이렉트
    
    # POST 요청 시 수정된 데이터를 처리
    if request.method == "POST":
        form = AnswerForm(request.POST, instance=answer)  # 기존 데이터를 담아 폼을 생성
        
        # 폼이 유효한 경우
        if form.is_valid():
            # commit=False로 일단 객체만 생성하고 DB에는 저장하지 않음
            answer = form.save(commit=False)
            answer.modify_date = timezone.now()  # 수정 시간 설정
            answer.save()  # 수정된 답변을 DB에 저장
            
            # 수정된 답변으로 질문 상세 페이지로 리다이렉트하고 앵커로 해당 답변 위치로 이동
            return redirect('{}#answer_{}'.format(resolve_url('pybo:detail', question_id=answer.question.id), answer.id))
    
    # GET 요청 시 기존 데이터를 담아 폼을 생성
    else:
        form = AnswerForm(instance=answer)
    
    # 템플릿에 전달할 데이터 설정
    context = {'answer': answer, 'form': form}
    
    # 'pybo/answer_form.html' 템플릿을 렌더링하여 응답 반환
    return render(request, 'pybo/answer_form.html', context)

########################################################################################################

@login_required(login_url='common:login')  # 로그인 상태에서만 접근 가능하게 설정
def answer_delete(request, answer_id):
    """ pybo 답변 삭제 """
    
    # answer_id에 해당하는 Answer 객체를 가져오고, 없으면 404 에러 반환
    answer = get_object_or_404(Answer, pk=answer_id)
    
    # 현재 로그인한 사용자가 답변 작성자가 아닐 경우 에러 메시지를 출력
    if request.user != answer.author:
        messages.error(request, '삭제권한이 없습니다')
    
    # 답변 작성자가 맞으면 답변을 삭제
    else:
        answer.delete()
    
    # 삭제 후 질문 상세 페이지로 리다이렉트
    return redirect('pybo:detail', question_id=answer.question.id)

########################################################################################################

@login_required(login_url='common:login')  # 로그인 상태에서만 접근 가능하게 설정
def answer_vote(request, answer_id):
    """ pybo 답변 추천 """
    
    # answer_id에 해당하는 Answer 객체를 가져오고, 없으면 404 에러 반환
    answer = get_object_or_404(Answer, pk=answer_id)
    
    # 답변 작성자가 본인일 경우 추천 불가 처리
    if request.user == answer.author:
        messages.error(request, '본인이 작성한 글은 추천할수 없습니다')
    
    # 본인이 작성한 글이 아닌 경우 추천 처리
    else:
        answer.voter.add(request.user)  # 현재 로그인한 사용자를 추천자 목록에 추가
    
    # 추천 후 질문 상세 페이지로 리다이렉트하고 앵커로 해당 답변 위치로 이동
    return redirect('{}#answer_{}'.format(resolve_url('pybo:detail', question_id=answer.question.id), answer.id))

########################################################################################################
