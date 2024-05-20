from datetime import datetime
import logging
from django.http import HttpResponse
from django.shortcuts import render
from .forms import order_registerForm

logger = logging.getLogger(__name__)

def start(request):
    title = 'Главное меню!'
    if request.method == 'POST':
        form = order_registerForm(request.POST, request.FILES)
        if form.is_valid():
            # Сначала сохраняем форму, чтобы получить ID
            instance = form.save(commit=False)
            instance.save()

            # Формирование значения для Numbers
            instance.Numbers = datetime.today().strftime("%d%m%y") + '-' + str(instance.id).zfill(2)
            instance.save()

            # Логирование данных из формы
            nomer_proekta = instance.nomer_proekta
            naimenovanie_proekta = instance.naimenovanie_proekta
            nomer_zakaza = instance.nomer_zakaza
            proizvodstvo = instance.proizvodstvo
            uploaded_file = instance.file

            print(nomer_proekta, nomer_zakaza, naimenovanie_proekta, proizvodstvo, uploaded_file)

            logger.debug(f'Номер проекта: {nomer_proekta}')
            logger.debug(f'Наименование проекта: {naimenovanie_proekta}')
            logger.debug(f'Номер заказа: {nomer_zakaza}')
            logger.debug(f'Производство: {proizvodstvo}')
            logger.debug(f'Загруженный файл: {uploaded_file.path}')

            # Вывод пути к файлу на страницу или в лог
            return HttpResponse(f'Файл загружен по пути: {uploaded_file.path}')
        else:
            print("Форма не валидна")
            print(form.errors)  # Вывод ошибок формы
            print(request.POST)  # Вывод данных POST-запроса
            logger.error('Форма не валидна')
    else:
        form = order_registerForm()

    content = {
        'title': title,
        'form': form,
    }

    logger.info("Страница загружена успешно")
    print("Страница загружена успешно")
    return render(request, 'productions/start.html', content)
