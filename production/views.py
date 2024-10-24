from datetime import datetime
import os

from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import order_registerForm, calculation_of_materialsForm
from .materials.creation_of_documents import rashet
import shutil
from .materials.materials_simple import vvod
from .materials.to_exl_main_mat import preobrazovanie
from django.contrib import messages


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
                          }
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
                instance.save()

                # Выполнение расчета и создание Excel через FileHandler
                file_handler = FileHandler(numbers=instance.Numbers)
                archive_path = file_handler.handle_materials(instance)

                # Отправляем архив пользователю
                with open(archive_path, 'rb') as archive_file:
                    response = HttpResponse(archive_file.read(), content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename={os.path.basename(archive_path)}'
                    return response
            else:
                print("Форма не валидна")
                print(form2.errors)
                print(request.POST)


    content = {
        'title': title,
        'attr': attr,
    }

    print("Страница загружена успешно")
    return render(request, 'productions/start.html', content)


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
                                    params['Nflanc'], params['Lsvar_izd']])
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

    def handle_materials(self, instance):
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
        preobrazovanie(result, [seria, material, nominal, dlina, Nstik, Nsekc, Nkon_zag, Nflanc, Lsvar_izd])

        # Сохраняем сгенерированный Excel файл
        excel_filename = f'Расчет материалов_{self.numbers}.xls'
        excel_file_path = os.path.join(base_path, excel_filename)
        self.save_file('example2.xls', excel_file_path)

        # Создаем архив и возвращаем путь к нему
        archive_path = self.create_archive(base_path, os.path.dirname(base_path))
        return archive_path


'''class FileHandler:

    def __init__(self, fname, line_zakaz):
        # Инициализация класса с переданными параметрами
        self.fname = fname
        self.line_zakaz = line_zakaz

    def save_file_dialog(self, spisok, Nombers):

        # Создание архива и сохранение его в указанной директории
        def create_archive(src_dir, dest_dir):
            """
            Создает архив из указанной директории.

            :param src_dir: Директория, которую нужно архивировать.
            :param dest_dir: Директория, куда будет сохранен архив.
            :return: Полный путь к созданному архиву.
            """
            # Определяем имя архива
            archive_name = os.path.basename(src_dir)
            archive_path = os.path.join(dest_dir, archive_name)

            # Создаем архив
            shutil.make_archive(archive_path, 'zip', src_dir)

            # Возвращаем путь к архиву с расширением .zip
            return f"{archive_path}.zip"

        # Вложенная функция для сохранения файла
        def save_file(src_file, dest_file, remove_src):
            print(f'Сохранить файл: {dest_file}')  # Вывод пути сохранения файла
            shutil.copyfile(src_file, dest_file)  # Копирование файла в новую директорию
            if remove_src:  # Проверка, нужно ли удалить исходный файл
                print(f'Удаляем файл: {src_file}')  # Сообщение об удалении файла
                os.remove(src_file)  # Удаление исходного файла
            else:
                print(f'Не удаляем файл: {src_file}')  # Сообщение о сохранении файла

        def create_directory(path):
            if not os.path.exists(path):  # Проверка наличия директории
                print(f'Записываем новую папку: {path}')  # Сообщение о создании новой директории
                os.makedirs(path)  # Создание новой директории
            else:
                print(f'Папка уже существует: {path}')  # Сообщение о существующей директории

        # Путь к новой директории в корне проекта
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../unload', Nombers))
        create_directory(base_path)  # Создание новой директории

        # Список стандартных папок
        subfolders = ['1. Ведомость деталей', '2. КОВ', '3. Наклейки', '4. Программы', '5. Расходники',
                      '6. Чертежи', '7. Материалы', '8. Спецификация заказа']
        for subfolder in subfolders:  # Проверка наличия каждой стандартной папки
            create_directory(os.path.join(base_path, subfolder))  # Создание стандартной папки, если её нет

        # Сохранение файлов из spisok[0]
        for item in spisok[0]:  # Итерация по списку файлов для сохранения
            print(item)
            subfolder_index = item[0]  # Индекс подкаталога
            print(subfolder_index)
            file_name = item[1]  # Имя файла

            dest_path = os.path.join(base_path, subfolders[subfolder_index],
                                     file_name)  # Создание нового пути для файла
            save_file(file_name, dest_path, remove_src=True)  # Сохранение файла в новый путь

        # Обработка и сохранение файлов из spisok[1]
        for i, params in spisok[1].items():  # Итерация по элементам словаря spisok[1]
            result = vvod(params['seria'], params['material'], params['nominal'], params['dlina'],
                          params['Nstik'], params['Nsekc'], params['Nkon_zag'], params['Nflanc'],
                          params['Lsvar_izd'], 4).fg()  # Ввод данных для расчета материалов
            print(f'Преобразование: {result}')  # Вывод результатов преобразования
            preobrazovanie(result, [params['seria'], params['material'], params['nominal'], params['dlina'],
                                    params['Nstik'], params['Nsekc'], params['Nkon_zag'],
                                    params['Nflanc'], params['Lsvar_izd']])  # Преобразование данных для Excel
            new_name = (f'Расчет материалов Заказ №{self.line_zakaz} Этап №{i} '
                        f'{params["seria"]}-{params["material"]}-{params["nominal"]}-{params["dlina"]}.xls')  # Создание нового имени файла
            save_file("example2.xls", os.path.join(base_path, subfolders[6], new_name),
                      remove_src=True)  # Сохранение файла с новым именем

        # Сохранение исходного файла в папку "8. Спецификация заказа"
        original_file_path = self.fname.path if hasattr(self.fname, 'path') else self.fname
        save_file(original_file_path, os.path.join(base_path, subfolders[7], os.path.basename(original_file_path)),
                  remove_src=False)
        # Создаем архив из директории
        archive_path = create_archive(base_path, os.path.dirname(base_path))
        print(f'Архив создан: {archive_path}')
        return archive_path'''