# reg/urls.py
from django.urls import path, include

from . import views
from app_users.views import AnotherLogoutView

urlpatterns = [
    path('glavn', views.glavn, name='home'),
    path('regis', views.regis, name='regis'),
    path('companyList', views.companyList, name='companyList'),
    path('logout', AnotherLogoutView.as_view(), name='logout'),
    path('sdelka/<int:sdelka_id>', views.sdelka, name='sdelka'),
]
