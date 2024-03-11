from django.urls import path, include
from app_users.views import AnotherLoginView, AnotherLogoutView

urlpatterns = [
    path('', AnotherLoginView.as_view(), name='another_login'),
    path('logout', AnotherLogoutView.as_view(), name='another_logout'),
    path('', include('reg.urls'), name='home'),
]