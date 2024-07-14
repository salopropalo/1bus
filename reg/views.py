from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from .models import regModel, companyModel
from .forms import transactionListForm, transactionForm, companyForm
from django.db.models import Q
import logging
from datetime import datetime
from django.http import HttpResponse

logger = logging.getLogger(__name__)
def home(request):
    title = 'Главная!'
    content = {
        #'status_html': regModel.STATUS,  # статус для формы HTML
        #'add': add,  # статус пользователя для определения его прав на просмотр и изменения
        'title': title,  # заголовок списка
        #'data_cards': dateReg,  # данные для отображения в карточках
        #'form': form,  # данные для отображения в карточках
        #'error': error,  #
        #'title2': 'Регистрация нового проекта',  # заголовок страницы
        #'name_str': 'transactionList'  # заголовок страницы
    }
    logger.info("test")
    return render(request, 'reg/home.html', content)

# Сделки
def transactionList(request):
    error = ''
    # Сортировка только тех проектов, которые созданы активным пользователем
    # для Админа
    if request.user.has_perm('reg.delete_regmodel'):
        dateReg = regModel.objects.all()
        title = 'Список всех сделок'
        add = True
    # для продавцов
    elif request.user.has_perm('reg.add_regmodel'):
        dateReg = regModel.objects.filter(Responsible=request.user.get_full_name())
        title = 'Список Ваших сделок'
        add = True
    elif request.user.has_perm('reg.view_regmodel'):
        dateReg = regModel.objects.filter(Status='3')
        title = 'Список согласованных сделок'
        add = False
    else:
        raise PermissionDenied

    # если был запрос на создание нового проекта, мы заполняем его в базу данных
    if request.method == 'POST':
        print('POST', request.POST)
        form = transactionListForm(request.POST)

        # Проверяем что нам вернулось с post запросом со страницы
        if 'modal' in request.POST:
            if form.is_valid():
                instance = form.save(commit=False)
                instance.save()
                print(request.user.get_full_name())
                instance.Numbers = datetime.today().strftime("%d%m%y") + '-' + str(instance.id).zfill(2) + 'C'
                instance.Responsible = request.user.get_full_name()
                instance.save()
                return redirect('transactionList')
            else:
                error = 'Что то не так с запросом на создание проекта'
        # Открываем карточку
        elif 'card' in request.POST:
            print(request.POST['card'])
            return redirect('transaction', request.POST['card'])
        else:
            error = 'POST запрос с ошибкой!'

    if request.method == 'GET':
        # поиск
        if 'q' in request.GET:
            # Получение вводимой информации в поисковике и запрос в БД
            search_term = request.GET['q']
            print(search_term, dateReg)
            dateReg = dateReg.filter(
                Q(Numbers__iregex=search_term) |
                Q(Name__iregex=search_term) |
                Q(Responsible__iregex=search_term) |
                Q(Status__iregex=search_term)
            )
        # сортировка по статусам
        elif 'sortirovka' in request.GET:
            selected_sorting = request.GET['sortirovka']
            if selected_sorting in ['всё']:
                if request.user.has_perm('reg.delete_regmodel'):
                    dateReg = dateReg.all()
                elif request.user.has_perm('reg.add_regmodel'):
                    dateReg = dateReg.filter(Responsible=request.user.get_full_name())
                elif not request.user.has_perm('reg.add_regmodel'):
                    dateReg = dateReg.filter(Status__in=['3', '4'])
                else:
                    raise PermissionDenied
            else:
                dateReg = dateReg.filter(Status=selected_sorting)

    form = transactionListForm()
    content = {
        'status_html': regModel.STATUS,     # статус для формы HTML
        'add': add,                     # статус пользователя для определения его прав на просмотр и изменения
        'title': title,                 # заголовок списка
        'data_cards': dateReg,          # данные для отображения в карточках
        'form': form,                   # данные для отображения в карточках
        'error': error,                 #
        'title2': 'Регистрация нового проекта',  # заголовок страницы
        'name_str': 'transactionList'  # заголовок страницы
    }

    return render(request, 'reg/list.html', content)

# Компании
def companyList(request):
    error = ''
    # Сортировка только тех проектов, которые созданы активным пользователем
    # для Админа
    if request.user.has_perm('reg.delete_companymodel'):
        dateReg = companyModel.objects.all()
        title = 'Список всех проектов'
        add = True
    # для продавцов
    elif request.user.has_perm('reg.add_companymodel'):
        dateReg = companyModel.objects.filter(Responsible=request.user.get_full_name())
        title = 'Список Ваших компаний'
        add = True
    elif request.user.has_perm('reg.view_companymodel'):
        dateReg = companyModel.objects.filter(Status='действующая компания')
        title = 'Список действующих компаний'
        add = False
    else:
        raise PermissionDenied

    # если был запрос на создание нового проекта, мы заполняем его в базу данных
    if request.method == 'POST':
        form = companyForm(request.POST)

        # Проверяем что нам вернулось с post запросом со страницы
        if 'modal' in request.POST:
            if form.is_valid():
                instance = form.save(commit=False)
                instance.save()
                instance.Responsible = request.user.get_full_name()
                instance.Numbers = datetime.today().strftime("%d%m%y") + '-' + str(instance.id).zfill(2) + 'K'
                instance.save()
                return redirect('companyList')
            else:
                # Выводим ошибки формы в консоль
                print("POST запрос с ошибкой!")
                print(form.errors)  # выводим ошибки формы
                return render(request, 'reg/list.html',
                              {'form': form, 'name_str': 'companyList'})  # вернуться на страницу с формой и передать ошибки

    if request.method == 'GET':
        print('сообщение', dateReg)
        if 'q' in request.GET:
            # Получение вводимой информации в поисковике и запрос в БД
            search_term = request.GET['q']
            dateReg = dateReg.filter(
                Q(INN__iregex=search_term) |
                Q(Responsible__iregex=search_term) |
                Q(Name__iregex=search_term) |
                Q(Status__iregex=search_term)
            )
        elif 'sortirovka' in request.GET:
            selected_sorting = request.GET['sortirovka']
            if selected_sorting in ['всё']:
                # для группы пользователей у которых есть права на удаление
                if request.user.has_perm('reg.delete_companymodel'):
                    dateReg = dateReg.all()
                # для группы пользователей у которых есть права на добавление
                elif request.user.has_perm('reg.add_companymodel'):
                    dateReg = dateReg.filter(Responsible=request.user.get_full_name())
                # для группы пользователей у которых нет прав на добавление или удаление
                elif not request.user.has_perm('reg.add_companymodel'):
                    dateReg = dateReg.filter(Status='действующая компания')
                else:
                    raise PermissionDenied
            else:
                dateReg = dateReg.filter(Status=selected_sorting)

    form = companyForm
    content = {
        'status_html': companyModel.STATUS,  # статус для формы HTML
        'add': add,  # статус пользователя для определения его прав на просмотр и изменения
        'title': title,  # заголовок списка
        'data_cards': dateReg,  # данные для отображения в карточках
        'form': form,  # данные для отображения в карточках
        'error': error,  #
        'title2': 'Регистрация новой компании',  # заголовок страницы
        'name_str': 'companyList'
    }
    return render(request, 'reg/list.html', content)


# _____________________________________________________________________________________________________________________
# Карточка сделки
def transaction(request, transaction_id):
    obj = regModel.objects.get(id=transaction_id)
    title = 'Сделка №' + obj.Numbers + ' ' + obj.Name
    date = obj.Date_born
    responsible = obj.Responsible
    date_born = date.strftime('%d.%m.%Y')

    print(obj)

    if obj.Customer_company is None:
        customer_company = 'Не присвоено'
    else:
        customer_company = companyModel.objects.get(Name=obj.Customer_company_id)

    adres = obj.Adres_obj
    status = obj.Status

    for element in regModel.STATUS:
        if status in element:
            status_name = element[1]
            print(status_name, status)
            break
        else:
            status_name = 'Не определён'

    # Если статус переведен из первого состояния, то его нельзя редактировать и кнопки редактирования не будет
    if status == '1':
        name_button = 'Отправить на проверку'
        add = True
    elif status == '2':
        name_button = 'Создать Заказ'
        add = False
    elif status == '3':
        name_button = 'Закрыть сделку'
        add = False
    elif status == '4':
        name_button = 'Возобновить работу'
        add = False
    else:
        name_button = 'Ошибка'
        add = False

    # Если был запрос на создание новой сделки, обрабатываем POST запрос
    if request.method == 'POST':
        form = transactionListForm(request.POST)

        # Проверяем что нам вернулось с post запросом со страницы
        if 'izm' in request.POST:
            if form.is_valid():
                obj.Customer_company = form.cleaned_data['Customer_company']
                obj.Seller_company = form.cleaned_data['Seller_company']
                obj.Adres_obj = form.cleaned_data['Adres_obj']
                obj.save()

                return redirect('companyList')
        else:
            error = 'POST запрос с ошибкой!'
    else:
        form = transactionListForm()

    content = {
        'form': form,
        'title': title,
        'date_born': date_born,
        'responsible': responsible,
        'customer_company': customer_company,
        'adres': adres,
        'status': status,
        'status_name': status_name,
        'add': add,
        'name_button': name_button,
        'title2': 'Внесение изменений'
    }
    return render(request, 'reg/sdelka.html', content)

