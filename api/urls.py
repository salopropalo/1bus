
from django.urls import path
from . import views

urlpatterns = [
    path('csrf/', views.csrf_token, name='api_csrf'),
    path('login/', views.login_view, name='api_login'),
    path('logout/', views.logout_view, name='api_logout'),
    path('me/', views.current_user, name='api_current_user'),
]
