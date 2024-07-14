from datetime import datetime
import os

from django.http import HttpResponse
from django.shortcuts import render
from .forms import order_registerForm
from .materials.creation_of_documents import rashet
import shutil
from .materials.materials_simple import vvod
from .materials.to_exl_main_mat import preobrazovanie


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
            instance.Responsible = request.user.get_full_name()
            instance.Name = "Комплект документов"
            instance.save()
            # Логирование данных из формы
            nomer_proekta = instance.nomer_proekta
            naimenovanie_proekta = instance.naimenovanie_proekta
            nomer_zakaza = instance.nomer_zakaza
            proizvodstvo = instance.proizvodstvo
            uploaded_file = instance.file
            print(uploaded_file.path)
            number = instance.Numbers
            print(nomer_proekta, nomer_zakaza, naimenovanie_proekta, proizvodstvo, uploaded_file, number)
            spisok = rashet([nomer_zakaza, nomer_proekta, naimenovanie_proekta],
                            uploaded_file.path, proizvodstvo, number).zapusk()
            print(spisok)
            archive_path = FileHandler(uploaded_file, nomer_zakaza).save_file_dialog(spisok, instance.Numbers)
            # Отправка архива пользователю
            with open(archive_path, 'rb') as archive_file:
                response = HttpResponse(archive_file.read(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename={os.path.basename(archive_path)}'
                return response
        else:
            print("Форма не валидна")
            print(form.errors)  # Вывод ошибок формы
            print(request.POST)  # Вывод данных POST-запроса
            # logger.error('Форма не валидна')

    else:
        form = order_registerForm()

    content = {
        'title': title,
        'form': form,
    }

    print("Страница загружена успешно")
    return render(request, 'productions/start.html', content)


class FileHandler:

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
        return archive_path