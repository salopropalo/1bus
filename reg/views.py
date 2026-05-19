from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from .models import regModel, companyModel
from .forms import transactionListForm, transactionForm, companyForm
from django.db.models import Q
from production.models import (Specification, seriesModel, nominalModel, conductorsModel, materialModel,
                               NameNomenclature, ComponentsModel)
import logging
from datetime import datetime
from collections import defaultdict
from decimal import Decimal
from django.shortcuts import get_object_or_404
from itertools import groupby
from django import template
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
                instance.Numbers = datetime.today().strftime("%m%y") + '-' + str(instance.id).zfill(2) + 'C'
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
    obj = get_object_or_404(
        regModel.objects.select_related('Customer_company', 'Seller_company'),
        id=transaction_id
    )
    name = obj.Name
    number = obj.Numbers
    sales = obj.sales or 0
    nds = Decimal('0.22')
    discount_multiplier = Decimal(str((100 - sales) / 100))  # скидка: 10% → 0.90
    responsible = obj.Responsible
    now_date = datetime.today().strftime('%d.%m.%Y')
    now_time = datetime.today().strftime('%H.%M')

    # Данные для фильтров (номиналы, проводники, материалы)
    nominal = list(nominalModel.objects.all().values_list('Name', flat=True))
    conductors = list(conductorsModel.objects.all().values_list('quantity', flat=True))
    material = list(materialModel.objects.all().values_list('Designation', flat=True))
    def transaction(request, transaction_id):
        obj = get_object_or_404(regModel.objects.select_related('Customer_company', 'Seller_company'),
                                id=transaction_id)
    # Сортировка номенклатуры по категориям
    nomenclature = NameNomenclature.objects.all().order_by('category', 'Name')

    # -------- РАСЧЁТ СПЕЦИФИКАЦИИ ----------
    specifications = Specification.objects.filter(transaction=obj, status='active').select_related(
        'article', 'article__Name'
    )

    line_counts = defaultdict(int)
    line_totals = defaultdict(Decimal)
    line_weight = defaultdict(Decimal)
    line_length = defaultdict(Decimal)

    total_quantity = 0
    total_sum = Decimal('0.00')
    total_weight = Decimal('0.00')
    total_length = Decimal('0.00')
    total_nds = Decimal('0.00')

    items_by_line = defaultdict(list)

    for spec in specifications:
        article = spec.article
        if not article:
            continue

        quantity = spec.quantity or 0

        # 1. Цена без НДС со скидкой
        base_price = article.price.amount if article.price else Decimal('0.00')
        price_no_nds = base_price * discount_multiplier

        # 2. НДС за единицу
        nds_per_unit = price_no_nds * nds

        # 3. Цена с НДС за единицу
        price_with_nds = price_no_nds + nds_per_unit

        # 4. Сумма строки (с НДС, со скидкой)
        item_total = price_with_nds * quantity
        item_total_decimal = Decimal(str(item_total))

        # НДС всей строки
        item_nds_total = nds_per_unit * quantity

        # Вес
        weight_val = article.weight if article.weight is not None else Decimal('0.00')
        item_weight = weight_val * quantity

        # Длина – универсальная обработка
        length_val = Decimal('0.00')
        if article.Length is not None:
            if isinstance(article.Length, Decimal):
                length_val = article.Length
            else:
                try:
                    length_str = str(article.Length).strip().replace(',', '.')
                    length_val = Decimal(length_str)
                except (ValueError, TypeError):
                    length_val = Decimal('0.00')
        item_length = length_val * quantity

        # Накопление по линии
        line = spec.line or 'Без линии'
        line_counts[line] += quantity
        line_totals[line] += item_total_decimal
        line_weight[line] += item_weight
        line_length[line] += item_length
        total_nds += item_nds_total

        # Общие итоги
        total_quantity += quantity
        total_sum += item_total_decimal
        total_weight += item_weight
        total_length += item_length

        # Добавляем поля в объект спецификации для шаблона
        spec.price_no_nds = price_no_nds
        spec.nds_per_unit = nds_per_unit
        spec.price_with_nds = price_with_nds
        spec.total = item_total_decimal

        # Группировка
        items_by_line[line].append(spec)

    existing_lines = sorted(set(items_by_line.keys()))

    # Формируем line_list для шаблона
    line_list = [
        {'grouper': line, 'list': items}
        for line, items in items_by_line.items()
    ]
    # ---------------------------------------

    # Данные о компаниях
    customer_company = obj.Customer_company if obj.Customer_company else 'Не выбрано'
    seller_company = obj.Seller_company if obj.Seller_company else 'Не выбрано'
    adres = obj.Adres_obj
    status = obj.Status

    # Определение статуса
    status_name = next((el[1] for el in regModel.STATUS if status in el), 'Не определён')

    # Кнопки в зависимости от статуса
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

    # Обработка POST (изменение сделки или добавление спецификации)
    if request.method == 'POST':
        # 1. Отмена позиций
        if 'apply_cancel' in request.POST:
            cancelled_ids = request.POST.get('cancelled_ids', '')
            if cancelled_ids:
                ids_list = [int(id_str) for id_str in cancelled_ids.split(',') if id_str.strip().isdigit()]
                Specification.objects.filter(id__in=ids_list, transaction=obj).update(status='cancelled')
            return redirect('transaction', transaction_id=transaction_id)
        # 2. Изменение сделки
        elif 'izm' in request.POST:
            form = transactionListForm(request.POST)
            if form.is_valid():
                obj.Customer_company = form.cleaned_data['Customer_company']
                obj.Seller_company = form.cleaned_data['Seller_company']
                obj.Adres_obj = form.cleaned_data['Adres_obj']
                obj.save()
                return redirect('transaction', transaction_id=obj.id)  # исправлено: редирект на эту же сделку
        elif 'add_specification' in request.POST:
            # Создание новой позиции спецификации
            material_val = request.POST.get('material', '').strip()
            conductors_val = request.POST.get('conductors', '').strip()
            rated_current = request.POST.get('rated_current', '').strip()
            nomenclature_val = request.POST.get('nomenclature', '').strip()
            article = f"B-{material_val}-{conductors_val}-{rated_current}-{nomenclature_val}"
            # Здесь желательно проверить существование артикула в ComponentsModel
            Specification.objects.create(
                transaction=obj,
                article_id=article,
                line=request.POST.get('line', ''),
                quantity=request.POST.get('quantity', 1)
            )
            return redirect('transaction', transaction_id=transaction_id)

    form = transactionListForm()

    context = {
        'form': form,
        'name': name,
        'number': number,
        'responsible': responsible,
        'customer_company': customer_company,
        'seller_company': seller_company,
        'adres': adres,
        'status': status,
        'status_name': status_name,
        'add': add,
        'name_button': name_button,
        'title2': 'Внесение изменений',
        'now_date': now_date,
        'now_time': now_time,
        'nominal': nominal,
        'conductors': conductors,
        'material': material,
        'nomenclature': nomenclature,
        'existing_lines': existing_lines,
        # Данные спецификации
        'line_list': line_list,
        'line_counts': dict(line_counts),
        'line_totals': dict(line_totals),
        'line_weight': dict(line_weight),
        'line_length': dict(line_length),
        'total_sum': total_sum,
        'total_quantity': total_quantity,
        'total_weight': total_weight,
        'total_length': total_length,
        'sales': sales,
        'total_nds': total_nds,
        'nds_rate': 22,
    }
    return render(request, 'reg/sdelka.html', context)

