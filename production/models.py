from django.db import models
from datetime import datetime

from djmoney import money
from djmoney.models.fields import MoneyField
from django.core.validators import MinValueValidator, MaxValueValidator
from reg.models import companyModel
from django.core.validators import RegexValidator


# серии
class seriesModel(models.Model):
    Name = models.CharField('Наименование', max_length=10, unique=True)
    Standard = models.CharField('Стандарт', max_length=100)
    Description = models.CharField('Описание', max_length=255)

    # название строчки в таблице
    def __str__(self):
        if self.Name:
            return self.Name
        else:
            return 'Unnamed seriesModel'

    # название таблицы
    class Meta:
        verbose_name = 'Серия'


# материал
class materialModel(models.Model):
    TIP = (
        ('1', 'диэлектрик'),
        ('2', 'проводник'),
    )

    MAGNETIC = (
        ('1', 'диамагнетик'),
        ('2', 'парамагнетик'),
        ('3', 'ферромагнетик')
    )

    Name = models.CharField('Наименование', max_length=50, unique=True)
    Designation = models.CharField('Обозначение', max_length=100)
    tip = models.CharField('Тип',  max_length=255, default='1', choices=TIP)
    Magnetic = models.CharField('Магнитные свойства', max_length=255, default='1', choices=MAGNETIC, null=True)
    Resistance = models.CharField('Электрическое сопротивление, ОМ', max_length=100, null=True)
    Thermal_conductivity = models.CharField('Теплопроводность, Вт/(м*°С)', max_length=100, null=True)
    Heat_capacity = models.CharField('Теплоемкость, Дж/(кг*°С)', max_length=100, null=True)
    Description = models.CharField('Описание', max_length=255, null=True)

    # название строчки в таблице
    def __str__(self):
        return self.Name

    # название таблицы
    class Meta:
        verbose_name = 'Материал'


class nominalModel(models.Model):
    Name = models.CharField('Наименование', max_length=10)
    material = models.ForeignKey(materialModel,
                                         on_delete=models.CASCADE,
                                         to_field='Name',
                                         related_name='material',
                                         blank=True,  # Делаем поле необязательным
                                         null=True  # Добавляем null=True для обозначения пустого значения в базе данных
                                         )
    size = models.CharField('Габариты', max_length=15)
    link = models.FileField('файл')

    # название строчки в таблице
    def __str__(self):
        return self.Name

    # название таблицы
    class Meta:
        verbose_name = 'Номинал'


class conductorsModel(models.Model):
    Name = models.CharField('Наименование', max_length=10)
    quantity = models.CharField('Количество проводников', max_length=1)

    # название строчки в таблице
    def __str__(self):
        return self.quantity

    # название таблицы
    class Meta:
        verbose_name = 'Количество проводников'


# по идее это должно быть список заказов, но тут не хватает еще много чего к примеру, нужно чтобы были проекты,
# нужен журнал регистрации всех документов
class order_registerModel(models.Model):

    # ------ эти поля должны быть обязательны для любого документа или списка ------------------------------------------
    STATUS = (
        ('1', 'создан'),
        ('2', 'согласован'),
        ('3', 'в работе'),
        ('4', 'завершён')
    )   # Статус может быть создан до 5 пунктов

    PROIZVODSTVO = (
        ('1', 'Питон Кама'),
        ('2', 'Солярис')
    )

    Numbers = models.CharField('Номер', max_length=10)
    Name = models.CharField('Наименование', max_length=100)
    Date_born = models.DateField('Дата создания', auto_now=True)
    Responsible = models.CharField('Ответственный', max_length=100)
    Status = models.CharField('Статус', max_length=30, default='1', choices=STATUS)
    # -----------------------------------------------------------------------------------------------------------------

    nomer_proekta = models.CharField('Номер проекта', max_length=10)
    naimenovanie_proekta = models.CharField('Наименование проекта', max_length=40)
    nomer_zakaza = models.CharField('Номер заказа', max_length=10)
    proizvodstvo = models.CharField('Производственная площадка',  max_length=255, default='1', choices=PROIZVODSTVO)

    def file_upload_path(instance, filename):
        # Генерируем имя файла в формате "номер проекта-номер заказа-дата сегодня"
        result_string = datetime.today().strftime("%d%m%y")
        print(result_string)
        return f"uploads/calculation/{result_string}-{filename}"

    file = models.FileField(upload_to=file_upload_path)

    # название строчки в таблице
    def __str__(self):
        return self.Name

    # название таблицы
    class Meta:
        verbose_name = 'Список заказов'


# модель для создания конструкторского документа деталь НЕДОДЕЛАНО
class detailModel(models.Model):

    # ------ эти поля должны быть обязательны для любого документа ----------------------------------------------------
    STATUS = (
        ('1', 'действующая компания'),
        ('2', 'ликвидирована'),
    )  # Статус может быть создан до 5 пунктов

    Numbers = models.CharField('Номер', max_length=10)
    Name = models.CharField('Наименование', max_length=255, unique=True)
    Date_born = models.DateField('Дата создания', auto_now=True)
    Responsible = models.CharField('Ответственный', max_length=100)
    Status = models.CharField('Статус', max_length=255, default='1', choices=STATUS)
    # -----------------------------------------------------------------------------------------------------------------


class MaterialCalculationModel(models.Model):
    series = models.ForeignKey(seriesModel, on_delete=models.CASCADE, verbose_name="Серия шинопровода")
    conductor_material = models.ForeignKey(materialModel, on_delete=models.CASCADE, verbose_name="Материал проводника")
    nominal_current = models.ForeignKey(nominalModel, on_delete=models.CASCADE, verbose_name="Номинальный ток (А)")
    number_of_conductors = models.ForeignKey(conductorsModel, on_delete=models.CASCADE,
                                             verbose_name="Количество проводников")
    track_length = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Длина трассы (м)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    Responsible = models.CharField('Ответственный', max_length=100)

    def __str__(self):
        return f'{self.series.Name} - {self.conductor_material.Name} ({self.nominal_current} А)'

    class Meta:
        verbose_name = 'Расчет материалов'


class ProcessingOfShopSheetModel(models.Model):

    # ------ эти поля должны быть обязательны для любого документа или списка ------------------------------------------
    STATUS = (
        ('1', 'создан'),
        ('2', 'согласован'),
        ('3', 'в работе'),
        ('4', 'завершён')
    )   # Статус может быть создан до 5 пунктов

    PROIZVODSTVO = (
        ('1', 'Питон Кама'),
        ('2', 'Солярис')
    )

    Numbers = models.CharField('Номер', max_length=10)
    Name = models.CharField('Наименование', max_length=100)
    Date_born = models.DateField('Дата создания', auto_now=True)
    Responsible = models.CharField('Ответственный', max_length=100)
    Status = models.CharField('Статус', max_length=30, default='1', choices=STATUS)
    # -----------------------------------------------------------------------------------------------------------------

    nomer_proekta = models.CharField('Номер проекта', max_length=10)
    naimenovanie_proekta = models.CharField('Наименование проекта', max_length=40)
    nomer_zakaza = models.CharField('Номер заказа', max_length=10)
    nomer_etapa = models.CharField('Номер этапа', max_length=10)
    proizvodstvo = models.CharField('Производственная площадка',  max_length=255, default='1', choices=PROIZVODSTVO)

    def file_upload_path(instance, filename):
        # Генерируем имя файла в формате "номер проекта-номер заказа-дата сегодня"
        result_string = datetime.today().strftime("%d%m%y")
        print(result_string)
        return f"uploads/calculation/{result_string}-{filename}"

    file = models.FileField(upload_to=file_upload_path)

    # название строчки в таблице
    def __str__(self):
        return self.Name

    # название таблицы
    class Meta:
        verbose_name = 'Список рабочих ведомостей'


# единицы измерения
class UnitModel(models.Model):
    Name = models.CharField('Наименование', max_length=100)
    Sname = models.CharField('Сокращение', max_length=100)
    Code = models.DecimalField('Код', max_digits=5, decimal_places=0, null=True, blank=True)

    def __str__(self):
        return f'{self.Name} - {self.Sname}'

    class Meta:
        verbose_name = 'Единицы измерения'


# Номенклатура
class ComponentsModel(models.Model):

    # ------ эти поля должны быть обязательны для любого документа или списка ------------------------------------------
    STATUS = (
        ('1', 'новая'),
        ('2', 'действующая'),
        ('3', 'в архиве'),
    )   # Статус может быть создан до 5 пунктов

    CATEGORIES = (
        ('1', 'комплектующие'),
        ('2', 'товары'),
        ('3', 'хоз. расчеты')
    )

    Numbers = models.CharField('Номер', max_length=30)
    Name = models.CharField('Наименование', max_length=100)
    Date_born = models.DateField('Дата создания', auto_now=True)
    Responsible = models.CharField('Ответственный', max_length=100)
    Status = models.CharField('Статус', max_length=30, default='1', choices=STATUS)
    # ------------------------------------------------------------------------------------------------------------------

    price = MoneyField('Цена', max_digits=10, decimal_places=2, default_currency='RUB', null=True)
    # cost_price = MoneyField('Себестоимость', max_digits=10, decimal_places=2, default_currency='RUB')
    # discount = models.DecimalField(
    #     'Скидка (%)',
    #     max_digits=5,  # Максимум 3 цифры до запятой и 2 после (например, 100.00)
    #     decimal_places=2,
    #     default=57.00,  # По умолчанию скидка 0%
    #     validators=[
    #         MinValueValidator(0.00),  # Минимум 0%
    #         MaxValueValidator(100.00)  # Максимум 100%
    #     ]
    # )
    category = models.CharField('Категория', max_length=100, choices=CATEGORIES)
    file = models.FileField(null=True, blank=True)
    weight = models.DecimalField('Масса', max_digits=5, decimal_places=2, null=True, blank=True)
    unit = models.ForeignKey(UnitModel, on_delete=models.CASCADE, verbose_name='Ед. изм.', null=True, blank=True)
    Supplier = models.ForeignKey(companyModel, on_delete=models.CASCADE, verbose_name='Поставщик', null=True, blank=True)
    Supplier_designation = models.CharField('Обозначение поставщика', max_length=100, null=True, blank=True)

    def __str__(self):
        return f'{self.Name} - {self.Numbers}'

    class Meta:
        verbose_name = 'Номенклатура'