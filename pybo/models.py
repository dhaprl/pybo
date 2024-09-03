from django.db import models
from django.contrib.auth.models import User
# Create your models here.
#질문 모델, 제목은 200글자, 내용은 무한, 날짜
class Question(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name = 'author_question') #계정이 삭제되면 관련 글 모두 삭제, user을 voter도 참조하면 나중에 어떤 기준으로 할 지 장고가 알 수 없어서
    subject = models.CharField(max_length =200)
    content = models.TextField()
    create_date = models.DateTimeField()
    modify_date = models.DateTimeField(null = True, blank =True)
    voter =models.ManyToManyField(User,related_name = 'voter_question')
    def __str__(self):
        return self.subject

#대답 모델, 질문모델의 FK를 참조키로 사용(연결), 내용은 무한, 날짜 생성
class Answer(models.Model):
    author = models.ForeignKey(User, on_delete =models.CASCADE, related_name = 'author_answer')
    question = models.ForeignKey(Question, on_delete = models.CASCADE)
    content = models.TextField()
    create_date = models.DateTimeField()
    modify_date = models.DateTimeField(null = True, blank =True)
    voter = models.ManyToManyField(User,related_name = 'voter_answer')


class Comment(models.Model):
    author = models.ForeignKey(User, on_delete = models.CASCADE)
    content = models.TextField()
    create_date = models.DateTimeField()
    modify_date = models.DateTimeField(null=True, blank = True)
    question =models.ForeignKey(Question, null = True, blank =True, on_delete = models.CASCADE)
    answer = models.ForeignKey(Answer, null = True, blank = True, on_delete = models.CASCADE)
