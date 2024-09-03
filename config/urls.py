from cgitb import handler

from django.contrib import admin
from django.urls import path, include
from pybo.views import base_views

urlpatterns = [
    path('', base_views.index, name = "index"),
    path('admin/', admin.site.urls),
    path('pybo/', include('pybo.urls')),
    path('common/', include('common.urls')),

]
handler404 = 'common.views.page_not_found'