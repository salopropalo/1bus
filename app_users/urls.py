from django.urls import path, include
from app_users.views import AnotherLoginView, AnotherLogoutView, inactive_user_view, blocked_view

urlpatterns = [
    path('', AnotherLoginView.as_view(), name='another_login'),
    path('logout', AnotherLogoutView.as_view(), name='another_logout'),
    path('', include('reg.urls'), name='tasks'),
    path('inactive/', inactive_user_view, name='inactive_user'),
    path('blocked/', blocked_view, name='blocked'),
]