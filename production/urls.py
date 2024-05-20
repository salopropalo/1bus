# reg/urls.py
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.start, name='start'),                         # Главная страница для производства
]
