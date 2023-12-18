from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from .models import regModel, Stat, companyModel
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
        title = 'Список всех проектов'
        add = True
    # для продавцов
    elif request.user.has_perm('reg.add_regmodel'):
        dateReg = regModel.objects.filter(Responsible=request.user.get_full_name())
        title = 'Список Ваших проектов'
        add = True
    elif request.user.has_perm('reg.view_regmodel'):
        dateReg = regModel.objects.filter(Status='в работе')
        title = 'Список согласованных проектов'
        add = False
    else:
        raise PermissionDenied

    # если был запрос на создание нового проекта, мы заполняем его в базу данных
    if request.method == 'POST':
        form = regForm(request.POST)

        # Проверяем что нам вернулось с post запросом со страницы
        if 'modal' in request.POST:
            if form.is_valid():
                form = form.save(commit=False)
                form.Responsible = request.user.get_full_name()
                form.save()
                form.numbers = form.id
                form.save()
                return redirect('regis')
            else:
                error = 'Что то не так с запросом на создание проекта'
        # Если post запрос связан с выбранной из карточек сделкой
        elif 'sdelka' in request.POST:
            return redirect('sdelka', request.POST['sdelka'])
        # Если post запрос связан с сортировкой списка карточек сделок
        elif 'sortirovka' in request.POST:
            selected_sorting = request.POST['sortirovka']
            if selected_sorting in ['всё']:
                # для группы пользователей у которых есть права на удаление
                if request.user.has_perm('reg.delete_regmodel'):
                    dateReg = regModel.objects.all()
                # для группы пользователей у которых есть права на добавление
                elif request.user.has_perm('reg.add_regmodel'):
                    dateReg = regModel.objects.filter(Responsible=request.user.get_full_name())
                # для группы пользователей у которых нет прав на добавление или удаление
                elif not request.user.has_perm('reg.add_regmodel'):
                    dateReg = regModel.objects.filter(Status='в работе')
                    dateReg = dateReg.objects.filter(Status='завершён')
                else:
                    raise PermissionDenied
            else:
                dateReg = dateReg.filter(Status=selected_sorting)
        else:
            error = form.errors.as_data()
            print(form.errors.as_data())

    # поиск по карточкам
    if request.method == 'GET':
        if request.GET:
            search_term = request.GET['q']
            dateReg = regModel.objects.filter(
                Q(numbers__iregex=search_term) |
                Q(NameProg__iregex=search_term) |
                Q(Responsible__iregex=search_term) |
                Q(Customer_company__iregex=search_term) |
                Q(Adres_obj__iregex=search_term) |
                Q(Status__iregex=search_term)
            )

    form = regForm()
    content = {
        'status_html': Stat.STATUS,     # статус для формы HTML
        'add': add,                     # статус пользователя для определения его прав на просмотр и изменения
        'title': title,                 # заголовок списка
        'data_cards': dateReg,          # данные для отображения в карточках
        'form': form,                   # данные для отображения в карточках
        'error': error,                 #
        'title2': 'Регистрация нового проекта',  # заголовок страницы
        'name_str': 'regis'
    }

    return render(request, 'reg/reg.html', content)

def sdelka(request, sdelka_id):
    obj = regModel.objects.get(id=sdelka_id)
    title = 'Сделка №' + obj.numbers + ' ' + obj.NameProg
    date = obj.Date_born
    responsible = obj.Responsible
    date_born = date.strftime('%d.%m.%Y')
    customer_company = obj.Customer_company
    adres = obj.Adres_obj
    status = obj.Status
    form = sdelkaForm
    add = True

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

def companyList(request):
    error = ''
    title = ''
    add = False  # Предполагаю, что по умолчанию это False, если явно не указано иное

    if request.user.has_perm('reg.delete_companymodel'):
        dateReg = companyModel.objects.all()
        title = 'Список всех проектов'
        add = True
    elif request.user.has_perm('reg.add_companymodel'):
        dateReg = companyModel.objects.filter(Responsible=request.user)
        title = 'Список Ваших компаний'
        add = True
    elif request.user.has_perm('reg.view_companymodel'):
        dateReg = companyModel.objects.filter(Status='действующая компания')
        title = 'Список действующих компаний'
    else:
        raise PermissionDenied

    if request.method == 'POST':
        form = companyForm(request.POST)
        if 'modal' in request.POST:
            if form.is_valid():
                form = form.save(commit=False)
                form.Responsible = request.user.get_full_name()
                form.save()
                form.numbers = form.id
                form.save()
                return redirect('companyList')
            else:
                error = form.errors.as_data()
                print(form.errors.as_data())
        elif 'sortirovka' in request.POST:
            selected_sorting = request.POST['sortirovka']
            if selected_sorting == 'всё':
                dateReg = companyModel.objects.all()
            else:
                dateReg = dateReg.filter(Status=selected_sorting)
        else:
            error = 'POST запрос с ошибкой!'

    # поиск по карточкам
    if request.method == 'GET':
        if request.GET:
            search_term = request.GET['q']
            dateReg = companyModel.objects.filter(
                Q(INN__iregex=search_term) |
                Q(Name__iregex=search_term) |
                Q(Responsible__iregex=search_term) |
                Q(Nmae_Company__iregex=search_term) |
                Q(Legal_address__iregex=search_term) |
                Q(Status__iregex=search_term)
            )

    form = companyForm()
    content = {
        'status_html': companyModel.Stat.STATUS,
        'add': add,
        'title': title,
        'data_cards': dateReg,
        'form': form,
        'error': error,
        'title2': 'Регистрация новой компании',  # заголовок страницы
        'name_str': 'companyList'
    }
    return render(request, 'reg/company.html', content)

