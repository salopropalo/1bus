# reg/urls.py
from django.urls import path, include

from . import views
from app_users.views import AnotherLogoutView

urlpatterns = [
    path('tasks', views.tasks, name='tasks'),  # Cтраница с задачами
    #path('lending', views.lending, name='lending'), # Страница на которую попадаешь по умолчанию
    path('transactionList', views.transactionList, name='transactionList'),  # Список сделок
    path('companyList', views.companyList, name='companyList'),  # Список компаний
    path('logout', AnotherLogoutView.as_view(), name='logout'),  # Страничка выхода
    path('transactionList/sdelka<uuid:transaction_uuid>/', views.transaction, name='transaction'),  # Карточка сделки
    path('start/', include('production.urls'), name='start'),
]