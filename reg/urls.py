# reg/urls.py
from django.urls import path, include

from . import views
from app_users.views import AnotherLogoutView

urlpatterns = [
    path('home', views.home, name='home'),                         # Главная страница с задачами
    path('transactionList', views.transactionList, name='transactionList'),   # Список сделок
    path('companyList', views.companyList, name='companyList'),     # Список компаний
    path('logout', AnotherLogoutView.as_view(), name='logout'),     # Страничка выхода
    path('transaction/<int:transaction_id>', views.transaction, name='transaction'),    # Карточка сделки
]
