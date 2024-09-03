from timeit import template

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from config.settings import LOGIN_REDIRECT_URL

app_name =  'common'

"""장고에 있는 로그인 뷰 클래스를 사용해서 로그인,아웃 기능을 구현
 common/views 파일을 따로 수정할 것은 없지만 로그인 화면을 구현할 html은 만들어야 함
 기본 경로는 register/login.html이여서  template_name = "로그인.hteml이 있는 경로" 지정 필요
"""
urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name ='common/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name="logout"),
    path('signup/', views.signup, name="signup"),
]