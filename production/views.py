from datetime import datetime
import os

from django.http import HttpResponse
from .forms import order_registerForm, calculation_of_materialsForm, ProcessingOfShopSheetForm
from .materials.creation_of_documents import rashet
import shutil
from .materials.materials_simple import vvod
from .materials.to_exl_main_mat import preobrazovanie
from .materials.tools import exl_to_list, list_to_dict, writeToExl

from django.shortcuts import render

from django.apps import apps
regModel = apps.get_model('reg', 'regModel')


def start(request):
    title = 'Главное меню!'
    attr = {'order': {'nameModal': 'exampleModalOrder',
                      'textButton': 'Создать РД',
                      'titleModal': 'Введите данные и выберите файл *.xlxs',
                      'idModal': '0', 'from': order_registerForm(),
                      },
            'materials': {'nameModal': 'exampleModalMaterials',
                          'textButton': 'Создать расчет материалов',
                          'titleModal': 'Введите данные для расчета материалов',
                          'idModal': '1', 'from': calculation_of_materialsForm(),
                          },
            'shop': {'nameModal': 'exampleModalShop',
                     'textButton': 'Переработать в ЦВ',
                     'titleModal': 'Введите данные и выберите файл *.xlxs',
                     'idModal': '2', 'from': ProcessingOfShopSheetForm(),
                     },
            }

    if request.method == 'POST':
        form_type = request.POST.get('form_type')  # здесь 'form_type' - это имя, указанное в кнопке отправки формы
        print('POST', request.POST.get)
        print(form_type)

        # Создание ведомости материалов
        if form_type == 'order':
            form = order_registerForm(request.POST, request.FILES)

            if form.is_valid():
                # Сохраняем форму и получаем данные
                instance = form.save(commit=False)
                instance.save()

                # Формируем значение для номера и другой информации
                instance.Numbers = datetime.today().strftime("%d%m%y") + '-' + str(instance.id).zfill(2)
                instance.Responsible = request.user.get_full_name()
                instance.Name = "Комплект документов"
                instance.save()

                # Логирование данных из формы
                nomer_proekta = instance.nomer_proekta
                naimenovanie_proekta = instance.naimenovanie_proekta
                nomer_zakaza = instance.nomer_zakaza
                proizvodstvo = instance.proizvodstvo
                uploaded_file = instance.file

                # Выполнение расчета для заказа через rashet
                spisok = rashet([nomer_zakaza, nomer_proekta, naimenovanie_proekta], uploaded_file.path, proizvodstvo,
                                instance.Numbers).zapusk()

                # Создаем обработчик файлов и выполняем сохранение
                file_handler = FileHandler(fname=uploaded_file, line_zakaz=nomer_zakaza, numbers=instance.Numbers)
                archive_path = file_handler.handle_order(spisok)

                # Отправляем архив пользователю
                with open(archive_path, 'rb') as archive_file:
                    response = HttpResponse(archive_file.read(), content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(archive_path)}'
                    return response
            else:
                print("Форма не валидна")
                print(form.errors)

        # Создание расчета материалов
        if form_type == 'materials':
            form2 = calculation_of_materialsForm(request.POST)

            if form2.is_valid():
                instance = form2.save(commit=False)
                instance.save()

                # Формирование значения для Numbers
                instance.Numbers = datetime.today().strftime("%d%m%y") + '-' + str(instance.id).zfill(2)
                instance.Responsible = request.user.get_full_name()
                instance.Name = "Расчет материалов"
                delivery = request.POST.get('check')


                # Выполнение расчета и создание Excel через FileHandler
                file_handler = FileHandler(numbers=instance.Numbers)
                archive_path = file_handler.handle_materials(instance, delivery)

                # Отправляем архив пользователю
                with open(archive_path, 'rb') as archive_file:
                    response = HttpResponse(archive_file.read(), content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(archive_path)}'
                    return response
            else:
                print("Форма не валидна")
                print(form2.errors)
                print(request.POST)

        # Преобразование из маршрутной карты в цеховую ведомость
        if form_type == 'shop':
            form3 = ProcessingOfShopSheetForm(request.POST, request.FILES)

            if form3.is_valid():
                instance = form3.save(commit=False)
                instance.save()

                # Формируем значение для номера и другой информации
                instance.Numbers = datetime.today().strftime("%d%m%y") + '-' + str(instance.id).zfill(2)
                instance.Responsible = request.user.get_full_name()
                instance.Name = "Преобразование в ЦВ"
                instance.save()

                # Логирование данных из формы
                nomer_proekta = instance.nomer_proekta
                naimenovanie_proekta = instance.naimenovanie_proekta
                nomer_zakaza = instance.nomer_zakaza
                nomer_etapa = instance.nomer_etapa
                proizvodstvo = instance.proizvodstvo
                uploaded_file = instance.file
                instance.save()

                atribut = [nomer_zakaza, nomer_proekta, naimenovanie_proekta, nomer_etapa, proizvodstvo]

                item = exl_to_list('all', 'all', uploaded_file, 'Маршрутная карта').reading()
                item = list_to_dict(item, 'Переработать ЦВ').transformation()
                Fn = writeToExl(item, atribut, uploaded_file, 'Переработать ЦВ').Deleting_sheets()
                Fn = writeToExl(item, atribut, Fn, 'Переработать ЦВ').Write()

                # Указываем директорию для сохранения
                unload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../unload')
                if not os.path.exists(unload_dir):
                    os.makedirs(unload_dir)  # Создаем директорию, если ее нет

                # Формируем имя файла и полный путь для сохранения
                file_name = f'Заказ_{atribut[0]}_Этап_{atribut[3]}.xlsx'
                save_path = os.path.join(unload_dir, file_name)

                # Сохраняем файл Excel на сервере
                save_path = Fn
                print(f"Файл успешно сохранен по адресу: {save_path}")

                # Возвращаем файл пользователю
                with open(save_path, 'rb') as f:
                    response = HttpResponse(f.read(),
                                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = f'attachment; filename={file_name}'
                    return response
            else:
                print("Форма не валидна")
                print(form3.errors)
                print(request.POST)

    content = {
        'title': title,
        'attr': attr,
    }

    print("Страница загружена успешно")
    return render(request, 'production/start.html', content)


class FileHandler:

    def __init__(self, fname=None, line_zakaz=None, numbers=None):
        """
        Инициализация класса FileHandler с параметрами для файла и номера заказа.

        :param fname: Имя загруженного файла (только для 'order')
        :param line_zakaz: Номер заказа (для обоих order и materials)
        :param numbers: Уникальный номер документа или расчета (для обоих order и materials)
        """
        self.fname = fname
        self.line_zakaz = line_zakaz
        self.numbers = numbers

    def create_directory(self, path):
        """Создание директории, если она еще не существует."""
        if not os.path.exists(path):
            os.makedirs(path)

    def save_file(self, src_file, dest_file, remove_src=False):
        """Сохранение файла в указанную директорию."""
        shutil.copyfile(src_file, dest_file)
        if remove_src:
            os.remove(src_file)

    def create_archive(self, src_dir, dest_dir):
        """Создание архива из указанной директории."""
        archive_name = os.path.basename(src_dir)
        archive_path = os.path.join(dest_dir, archive_name)
        shutil.make_archive(archive_path, 'zip', src_dir)
        return f"{archive_path}.zip"

    def handle_order(self, spisok):
        """
        Обработка заказа (order), создание директорий и сохранение файлов.

        :param spisok: Список файлов для обработки.
        :return: Путь к созданному архиву.
        """
        # Путь к новой директории
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../unload', self.numbers))
        self.create_directory(base_path)

        # Список стандартных папок для заказов
        subfolders = ['1. Ведомость деталей', '2. КОВ', '3. Наклейки', '4. Программы', '5. Расходники',
                      '6. Чертежи', '7. Материалы', '8. Спецификация заказа']
        for subfolder in subfolders:
            self.create_directory(os.path.join(base_path, subfolder))

        # Сохранение файлов из spisok[0] по категориям
        for item in spisok[0]:
            subfolder_index = item[0]
            file_name = item[1]
            dest_path = os.path.join(base_path, subfolders[subfolder_index], file_name)
            self.save_file(file_name, dest_path, remove_src=True)

        # Обработка и сохранение материалов для spisok[1]
        for i, params in spisok[1].items():
            result = vvod(params['seria'], params['material'], params['nominal'], params['dlina'],
                          params['Nstik'], params['Nsekc'], params['Nkon_zag'], params['Nflanc'],
                          params['Lsvar_izd'], 4).fg()
            preobrazovanie(result, [params['seria'], params['material'], params['nominal'], params['dlina'],
                                    params['Nstik'], params['Nsekc'], params['Nkon_zag'],
                                    params['Nflanc'], params['Lsvar_izd']], 'pickup')
            new_name = (f'Расчет материалов Заказ №{self.line_zakaz} Этап №{i} '
                        f'{params["seria"]}-{params["material"]}-{params["nominal"]}-{params["dlina"]}.xls')
            self.save_file("example2.xls", os.path.join(base_path, subfolders[6], new_name), remove_src=True)

        # Сохранение исходного файла
        original_file_path = self.fname.path if hasattr(self.fname, 'path') else self.fname
        self.save_file(original_file_path, os.path.join(base_path, subfolders[7], os.path.basename(original_file_path)),
                       remove_src=False)

        # Создаем архив и возвращаем путь к нему
        archive_path = self.create_archive(base_path, os.path.dirname(base_path))
        return archive_path

    def handle_materials(self, instance, delivery):
        """
        Обработка расчета материалов (materials), создание директории и сохранение файла Excel.

        :param instance: Объект формы расчета материалов.
        :return: Путь к созданному архиву.
        """
        # Путь к новой директории
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../unload', self.numbers))
        self.create_directory(base_path)

        # Извлечение числовых значений
        seria = str(instance.series.Name)  # Серия
        material = str(instance.conductor_material.Designation)  # Материал проводника

        # Извлечение значения номинального тока из поля Name в модели nominalModel
        try:
            nominal = float(instance.nominal_current.Name)  # Преобразование строки в число
        except ValueError:
            # Если поле Name содержит нечисловое значение, можно добавить обработку ошибки
            raise ValueError(f"Невозможно преобразовать номинальный ток '{instance.nominal_current.Name}' в число.")

        dlina = float(instance.track_length)  # Длина трассы
        Nstik = dlina / 2.6  # Вычисляемое значение
        Nsekc = dlina / 2.6  # Вычисляемое значение
        Nkon_zag = 0  # Концевые заглушки
        Nflanc = 2  # Фланцы
        Lsvar_izd = dlina * 0.12  # Вычисляемое значение
        KolProv = int(instance.number_of_conductors.quantity)  # Количество проводников

        # Выполнение расчета через vvod и создание Excel-файла
        result = vvod(seria, material, nominal, dlina, Nstik, Nsekc, Nkon_zag, Nflanc, Lsvar_izd, KolProv).fg()
        preobrazovanie(result, [seria, material, nominal, dlina, Nstik, Nsekc, Nkon_zag, Nflanc, Lsvar_izd], delivery)

        # Сохраняем сгенерированный Excel файл
        excel_filename = f'Расчет материалов_{self.numbers}.xls'
        excel_file_path = os.path.join(base_path, excel_filename)
        self.save_file('example2.xls', excel_file_path)

        # Создаем архив и возвращаем путь к нему
        archive_path = self.create_archive(base_path, os.path.dirname(base_path))
        return archive_path
