import os
from django.db import models
from django.contrib.auth.models import User

# ==========================
# Question 모델 (질문 데이터)
# ==========================
class Question(models.Model):
    # 작성자: User 모델과 다대일 관계 (1명의 사용자가 여러 질문을 작성할 수 있음)
    # on_delete=models.CASCADE: User가 삭제되면 관련 질문도 함께 삭제됨
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author_question')
    
    # 질문 제목: 최대 200자, 반드시 입력해야 함
    subject = models.CharField(max_length=200, blank=False)
    
    # 질문 내용: 빈 값을 허용하지 않음
    content = models.TextField()
    
    # 질문 작성일시
    create_date = models.DateTimeField()
    
    # 질문 수정일시: 질문이 수정되지 않으면 null 값을 허용함
    modify_date = models.DateTimeField(null=True, blank=True)
    
    # 질문 조회수: 기본값은 0
    view_count = models.PositiveIntegerField(default=0)
    
    # 질문을 추천한 사용자들: 여러 사용자가 추천 가능 (ManyToManyField)
    voter = models.ManyToManyField(User, related_name='voter_question')
    
    # 이미지1: 질문에 첨부된 첫 번째 이미지, null과 빈 값을 허용하지 않음
    image1 = models.ImageField(upload_to='pybo/image1/', null=False, blank=False, verbose_name='업로드 이미지1')
    
    # 이미지2: 질문에 첨부된 두 번째 이미지, null과 빈 값을 허용하지 않음
    image2 = models.ImageField(upload_to='pybo/image2/', null=False, blank=False, verbose_name='업로드 이미지2')

    # save 메서드를 오버라이드하여 기존 이미지 파일을 삭제한 후 새로운 이미지로 교체
    def save(self, *args, **kwargs):
        # Question 객체가 이미 존재할 경우 (pk가 있는 경우)
        if self.pk:
            old_objects = Question.objects.get(pk=self.pk)
            # 기존 이미지1을 새 이미지로 대체할 경우, 이전 파일 삭제
            if old_objects.image1 and old_objects.image1 != self.image1:
                if os.path.isfile(old_objects.image1.path):
                    os.remove(old_objects.image1.path)
            # 기존 이미지2를 새 이미지로 대체할 경우, 이전 파일 삭제
            if old_objects.image2 and old_objects.image2 != self.image2:
                if os.path.isfile(old_objects.image2.path):
                    os.remove(old_objects.image2.path)
        # 장고의 기본 save 메서드 호출
        super(Question, self).save(*args, **kwargs)

    # 객체를 문자열로 표현할 때 질문 제목을 반환
    def __str__(self):
        return self.subject


# ==========================
# Answer 모델 (답변 데이터)
# ==========================
class Answer(models.Model):
    # 작성자: User 모델과 다대일 관계 (1명의 사용자가 여러 답변을 작성할 수 있음)
    # on_delete=models.CASCADE: User가 삭제되면 관련 답변도 함께 삭제됨
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author_answer')
    
    # 답변이 달린 질문과 연결: 질문이 삭제되면 답변도 함께 삭제됨
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    
    # 답변 내용
    content = models.TextField()
    
    # 답변 작성일시
    create_date = models.DateTimeField()
    
    # 답변 수정일시: 답변이 수정되지 않으면 null 값을 허용
    modify_date = models.DateTimeField(null=True, blank=True)
    
    # 답변을 추천한 사용자들: 여러 사용자가 답변을 추천할 수 있음 (ManyToManyField)
    voter = models.ManyToManyField(User, related_name='voter_answer')
    
    # 답변에 첨부된 이미지, null과 빈 값을 허용
    answer_image = models.ImageField(upload_to='pybo/answer_image', null=True, blank=True, verbose_name='업로드 이미지')

    # 객체를 문자열로 표현할 때 답변이 달린 질문의 제목을 반환
    def __str__(self):
        return self.question.subject


# ==========================
# Comment 모델 (댓글 및 대댓글 데이터)
# ==========================
class Comment(models.Model):
    # 작성자: User 모델과 다대일 관계
    # on_delete=models.CASCADE: User가 삭제되면 관련 댓글도 삭제됨
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # 댓글 내용
    content = models.TextField()
    
    # 댓글 작성일시
    create_date = models.DateTimeField()
    
    # 댓글 수정일시: 댓글이 수정되지 않으면 null 값을 허용
    modify_date = models.DateTimeField(null=True, blank=True)
    
    # 댓글이 달린 질문과의 관계: 질문에 댓글이 달린 경우, null 값을 허용 (질문에 대한 댓글)
    question = models.ForeignKey(Question, null=True, blank=True, related_name='comments', on_delete=models.CASCADE)
    
    # 댓글이 달린 답변과의 관계: 답변에 댓글이 달린 경우, null 값을 허용 (답변에 대한 댓글)
    answer = models.ForeignKey(Answer, null=True, blank=True, on_delete=models.CASCADE)
    
    # 부모 댓글: 대댓글 기능을 위해 부모 댓글을 참조, null 값을 허용 (대댓글 구조)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='replies', null=True, blank=True)

    # 객체를 문자열로 표현할 때 댓글 내용의 앞 20자를 반환
    def __str__(self):
        return self.content[:20]
