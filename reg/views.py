from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from .models import regModel, companyModel
from .forms import regForm, sdelkaForm, companyForm
from django.db.models import Q

def glavn(request):
    return render(request, 'reg/glavn.html', {'title': 'Главная страница'})

def regis(request):
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
        dateReg = regModel.objects.filter(Status='в работе')
        title = 'Список согласованных сделок'
        add = False
    else:
        raise PermissionDenied

    # если был запрос на создание нового проекта, мы заполняем его в базу данных
    if request.method == 'POST':
        print('POST', request.POST)
        form = regForm(request.POST)

        # Проверяем что нам вернулось с post запросом со страницы
        if 'modal' in request.POST:
            if form.is_valid():
                form = form.save(commit=False)
                form.Responsible = request.user.get_full_name()
                form.save()
                form.Numbers = form.id
                form.save()
                return redirect('regis')
            else:
                error = 'Что то не так с запросом на создание проекта'
        # Открываем карточку
        elif 'card' in request.POST:
            print(request.POST['card'])
            return redirect('sdelka', request.POST['card'])
        else:
            error = 'POST запрос с ошибкой!'

    if request.method == 'GET':
        # поиск
        if 'q' in request.GET:
            # Получение вводимой информации в поисковике и запрос в БД
            search_term = request.GET['q']
            dateReg = regModel.objects.filter(
                Q(numbers__iregex=search_term) |
                Q(NameProg__iregex=search_term) |
                Q(Responsible__iregex=search_term) |
                Q(Customer_company__Name_Company__iregex=search_term) |
                Q(Adres_obj__iregex=search_term) |
                Q(Status__iregex=search_term)
            )
        # сортировка по статусам
        elif 'sortirovka' in request.GET:
            selected_sorting = request.GET['sortirovka']
            if selected_sorting in ['всё']:
                if request.user.has_perm('reg.delete_regmodel'):
                    dateReg = regModel.objects.all()
                elif request.user.has_perm('reg.add_regmodel'):
                    dateReg = regModel.objects.filter(Responsible=request.user.get_full_name())
                elif not request.user.has_perm('reg.add_regmodel'):
                    dateReg = regModel.objects.filter(Status='в работе')
                    dateReg = dateReg.objects.filter(Status='завершен')
                else:
                    raise PermissionDenied
            else:
                dateReg = dateReg.filter(Status=selected_sorting)

    form = regForm()
    content = {
        'status_html': regModel.STATUS,     # статус для формы HTML
        'add': add,                     # статус пользователя для определения его прав на просмотр и изменения
        'title': title,                 # заголовок списка
        'data_cards': dateReg,          # данные для отображения в карточках
        'form': form,                   # данные для отображения в карточках
        'error': error,                 #
        'title2': 'Регистрация нового проекта',  # заголовок страницы
        'name_str': 'regis'  # заголовок страницы
    }

    return render(request, 'reg/reg.html', content)


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
                form = form.save(commit=False)
                form.Responsible = request.user.get_full_name()
                form.save()
                form.Numbers = form.id
                form.save()
                return redirect('companyList')
        # # Открываем карточку
        # elif 'card' in request.POST:
        #     return redirect('company', request.POST['card'])
        else:
            error = 'POST запрос с ошибкой!'

    if request.method == 'GET':
        if 'q' in request.GET:
            # Получение вводимой информации в поисковике и запрос в БД
            search_term = request.GET['q']
            dateReg = companyModel.objects.filter(
                Q(INN__iregex=search_term) |
                Q(Responsible__iregex=search_term) |
                Q(Name_Company__iregex=search_term) |
                Q(Legal_address__iregex=search_term) |
                Q(Status__iregex=search_term)
            )
        elif 'sortirovka' in request.GET:
            selected_sorting = request.GET['sortirovka']
            if selected_sorting in ['всё']:
                # для группы пользователей у которых есть права на удаление
                if request.user.has_perm('reg.delete_companymodel'):
                    dateReg = companyModel.objects.all()
                # для группы пользователей у которых есть права на добавление
                elif request.user.has_perm('reg.add_companymodel'):
                    dateReg = companyModel.objects.filter(Responsible=request.user.get_full_name())
                # для группы пользователей у которых нет прав на добавление или удаление
                elif not request.user.has_perm('reg.add_companymodel'):
                    dateReg = companyModel.objects.filter(Status='действующая компания')
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
    return render(request, 'reg/company.html', content)


def sdelka(request, sdelka_id):
    obj = regModel.objects.get(id=sdelka_id)
    title = 'Сделка №' + obj.Numbers + ' ' + obj.Name
    date = obj.Date_born
    responsible = obj.Responsible
    date_born = date.strftime('%d.%m.%Y')

    print(companyModel.objects.get(Name='ООО "ПИК "Солярис"'))
    print(obj)

    if obj.Customer_company is None:
        customer_company = 'Не присвоено'
    else:
        customer_company = companyModel.objects.get(Name=obj.Customer_company_id)

    adres = obj.Adres_obj
    status = obj.Status

    add = True

    # Если был запрос на создание новой сделки, обрабатываем POST запрос
    if request.method == 'POST':
        form = sdelkaForm(request.POST)

        # Проверяем что нам вернулось с post запросом со страницы
        if 'izm' in request.POST:
            if form.is_valid():
                obj.Customer_company = form.cleaned_data['Customer_company']
                obj.save()
                return redirect('companyList')
        else:
            error = 'POST запрос с ошибкой!'
    else:
        form = sdelkaForm()

    content = {
        'form': form,
        'title': title,
        'date_born': date_born,
        'responsible': responsible,
        'customer_company': customer_company,
        'adres': adres,
        'status': status,
        'add': add,
        'title2': 'Внесение изменений'
    }
    return render(request, 'reg/sdelka.html', content)

