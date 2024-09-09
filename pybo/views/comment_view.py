from django.contrib import messages  # 메시지 처리를 위한 모듈
from django.contrib.auth.decorators import login_required  # 로그인 필수 조건을 추가하는 데코레이터
from django.shortcuts import render, get_object_or_404, redirect  # 뷰 처리, 객체 조회, 리다이렉트 기능
from django.utils import timezone  # 시간 처리를 위한 유틸리티 모듈

from ..forms import CommentForm  # 댓글 작성 폼
from ..models import Question, Answer, Comment  # 모델 정의 (질문, 답변, 댓글)

# =======================================
# 질문에 대한 댓글 작성 뷰 (로그인 필요)
# =======================================
@login_required(login_url='common:login')  # 로그인이 필요하며, 로그인하지 않으면 로그인 페이지로 리다이렉트
def comment_create_question(request, question_id):
    """ pybo 질문에 댓글 작성 """
    # 댓글을 작성할 질문 객체를 조회 (존재하지 않으면 404 에러 발생)
    question = get_object_or_404(Question, pk=question_id)

    # POST 요청인 경우 댓글을 생성
    if request.method == "POST":
        form = CommentForm(request.POST)  # 폼에 전달된 데이터로 댓글 생성
        if form.is_valid():  # 폼 데이터가 유효할 경우
            comment = form.save(commit=False)  # DB에 바로 저장하지 않고 일단 폼에서 객체만 반환
            comment.author = request.user  # 댓글 작성자를 현재 로그인한 사용자로 설정
            comment.create_date = timezone.now()  # 댓글 작성 시간을 현재 시간으로 설정
            comment.question = question  # 댓글이 달린 질문을 설정
            comment.save()  # 댓글을 DB에 저장
        return redirect('pybo:detail', question_id=question.id)  # 댓글 작성 후 질문 상세 페이지로 리다이렉트
    else:
        # GET 요청인 경우 빈 폼을 생성하여 댓글 작성 페이지를 보여줌
        form = CommentForm()

    # 작성된 댓글과 대댓글을 조회하여 템플릿으로 전달
    comments = question.comments.filter(parent__isnull=True).order_by('create_date').prefetch_related('replies')
    comments_reply = Comment.objects.filter(parent__in=comments).order_by('create_date')

    # 템플릿에 전달할 데이터 설정
    context = {'form': form, 'comments': comments, 'comments_reply': comments_reply}
    return render(request, 'pybo/comment_form.html', context)  # 댓글 작성 페이지를 렌더링

# =======================================
# 질문 댓글 수정 뷰 (로그인 필요)
# =======================================
@login_required(login_url='common:login')  # 로그인이 필요하며, 로그인하지 않으면 로그인 페이지로 리다이렉트
def comment_modify_question(request, comment_id):
    """ pybo 질문 댓글 수정 """
    # 수정할 댓글 객체를 조회 (존재하지 않으면 404 에러 발생)
    comment = get_object_or_404(Comment, pk=comment_id)

    # 로그인한 사용자가 댓글 작성자가 아닌 경우 에러 메시지를 표시
    if request.user != comment.author:
        messages.error(request, '댓글 수정 권한이 없습니다.')
        return redirect('pybo:detail', question_id=comment.question.id)  # 권한이 없으면 질문 상세 페이지로 리다이렉트

    # POST 요청이면 댓글 수정 처리
    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)  # 기존 댓글 데이터를 포함한 폼 생성
        if form.is_valid():  # 폼 데이터가 유효할 경우
            comment = form.save(commit=False)  # DB에 바로 저장하지 않고 일단 폼에서 객체만 반환
            comment.author = request.user  # 댓글 작성자는 그대로 유지
            comment.modify_date = timezone.now()  # 댓글 수정 시간을 현재 시간으로 설정
            comment.save()  # 댓글을 DB에 저장 (수정 내용 적용)
            return redirect('pybo:detail', question_id=comment.question.id)  # 수정 후 질문 상세 페이지로 리다이렉트
    else:
        # GET 요청이면 기존 댓글 데이터를 폼에 담아서 수정 페이지를 보여줌
        form = CommentForm(instance=comment)

    # 템플릿에 전달할 데이터 설정
    context = {'form': form}
    return render(request, 'pybo/comment_form.html', context)  # 댓글 수정 페이지를 렌더링

# =======================================
# 질문 댓글 삭제 뷰 (로그인 필요)
# =======================================
@login_required(login_url='common:login')  # 로그인이 필요하며, 로그인하지 않으면 로그인 페이지로 리다이렉트
def comment_delete_question(request, comment_id):
    """ pybo 질문 댓글 삭제 """
    # 삭제할 댓글 객체를 조회 (존재하지 않으면 404 에러 발생)
    comment = get_object_or_404(Comment, pk=comment_id)

    # 로그인한 사용자가 댓글 작성자가 아닌 경우 에러 메시지를 표시
    if request.user != comment.author:
        messages.error(request, '댓글 삭제 권한이 없습니다.')
        return redirect('pybo:detail', question_id=comment.question.id)  # 권한이 없으면 질문 상세 페이지로 리다이렉트
    else:
        # 댓글 삭제 후 질문 상세 페이지로 리다이렉트
        comment.delete()  # 댓글을 삭제
        return redirect('pybo:detail', question_id=comment.question.id)  # 댓글 삭제 후 질문 상세 페이지로 리다이렉트
