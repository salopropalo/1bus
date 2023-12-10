from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from .models import regModel
from .forms import regForm, sdelkaForm

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
        print('POST', request.POST)
        form = regForm(request.POST)

        # Проверяем что нам вернулось с post запросом со страницы
        if 'new_sdelka' in request.POST:
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
            print('aaaaaaaaaaa', selected_sorting)
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
            error = 'POST запрос с ошибкой!'

    # поиск по карточкам
    if request.method == 'GET':
        if request.GET:
            a = request.GET['q']
            dateReg = regModel.objects.filter(numbers=a) | regModel.objects.filter(NameProg=a) \
                      | regModel.objects.filter(Responsible=a) | regModel.objects.filter(Customer_company=a) \
                      | regModel.objects.filter(Adres_obj=a) | regModel.objects.filter(Status=a)

    status_html = {1: 'всё', 2: 'создан', 3: 'согласован', 4: 'в работе', 5: 'завершён'}
    form = regForm()
    content = {
        'status_html': status_html,     # статус для формы HTML
        'add': add,                     # статус пользователя для определения его прав на просмотр и изменения
        'title': title,                 # заголовок списка
        'data_cards': dateReg,          # данные для отображения в карточках
        'form': form,                   # данные для отображения в карточках
        'error': error,                 #
        'title2': 'Регистрация нового проекта'  # заголовок страницы
    }

    return render(request, 'reg/reg.html', content)

def inreg(request):
    error = ''

    if request.method == 'POST':
        form = regForm(request.POST)

        if form.is_valid():
            form = form.save(commit=False)
            form.Responsible = request.user.get_full_name()
            form.save()
            form.numbers = form.id
            form.save()
            return redirect('regis')
        else:
            error = 'Чет ты натыкал???'

    form = regForm()
    content = {
        'form': form,
        'error': error,
        'title': 'Регистрация'
    }
    return render(request, 'reg/inreg.html', content)

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
