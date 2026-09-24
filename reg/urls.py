# reg/urls.py
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views
from app_users.views import AnotherLogoutView

urlpatterns = [
    # Cтраница с задачами
    path('tasks', views.tasks, name='tasks'),
    # Страничка выхода
    path('logout', AnotherLogoutView.as_view(), name='logout'),
    # Список сделок
    path('transactionList', views.transactionList, name='transactionList'),
    # Список компаний
    path('companyList', views.companyList, name='companyList'),
    # Карточка сделки
    path('transactionList/<uuid:transaction_uuid>/', views.transaction, name='transaction'),
    # Просмотр перед печатью
    path('transactionList/print/view/<uuid:transaction_uuid>/', views.transaction_print, name='transaction_print'),
    # Скачать PDF
    path('transactionList/print/pdf/<uuid:transaction_uuid>/', views.transaction_pdf, name='transaction_pdf'),
    # Карточка компании
    path('companyList/<uuid:company_uuid>/', views.company_card, name="company_card"),
    # Отпарвка на страницу производства
    path('start/', include('production.urls'), name='start'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)