from django import forms
from pybo.models import Question, Answer, Comment

########################################################################################################

# ===================================
# QuestionForm (질문 생성 및 수정 폼)
# ===================================
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question  # 이 폼이 Question 모델과 연결됨
        fields = ['subject', 'content', 'image1', 'image2']  # 사용할 필드 (제목, 내용, 이미지1, 이미지2)
        
        # 각 필드에 표시될 라벨을 정의
        labels = {
            'subject': '제목',
            'content': '내용',
            'image1': '이미지1',
            'image2': '이미지2',
        }

########################################################################################################

# ===================================
# AnswerForm (답변 생성 및 수정 폼)
# ===================================
class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer  # 이 폼이 Answer 모델과 연결됨
        fields = ['content', 'answer_image']  # 사용할 필드 (답변 내용, 첨부 이미지)
        
        # 각 필드에 표시될 라벨을 정의
        labels = {
            'content': '답변내용',
            'answer_image': '이미지',
        }

########################################################################################################

# ===================================
# CommentForm (댓글 및 대댓글 폼)
# ===================================
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment  # 이 폼이 Comment 모델과 연결됨
        fields = ['content', 'parent']  # 사용할 필드 (댓글 내용, 부모 댓글)

        # 각 필드에 표시될 라벨을 정의
        labels = {
            'content': '내용',
        }

    # 폼 초기화 시 부모 댓글을 처리하기 위한 생성자
    def __init__(self, *args, **kwargs):
        self.parent_comment = kwargs.pop('parent_comment', None)  # 부모 댓글을 kwargs에서 분리
        super().__init__(*args, **kwargs)

    # 댓글 저장 시 부모 댓글을 설정하는 save 메서드
    def save(self, commit=True):
        comment = super().save(commit=False)  # 기본 save 메서드 호출 전에 데이터베이스에 저장하지 않음
        if self.parent_comment:
            comment.parent = self.parent_comment  # 부모 댓글이 존재하면 이를 설정
        if commit:
            comment.save()  # 데이터베이스에 댓글 저장
        return comment

########################################################################################################
