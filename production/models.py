from django.db import models
from datetime import datetime

from djmoney import money
from djmoney.models.fields import MoneyField
from django.core.validators import MinValueValidator, MaxValueValidator
from reg.models import companyModel
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

# единицы измерения
class UnitModel(models.Model):
    id = models.AutoField(primary_key=True)
    Name = models.CharField('Наименование', max_length=100)
    Sname = models.CharField('Сокращение', max_length=100)
    Code = models.DecimalField('Код', max_digits=5, decimal_places=0, null=True, blank=True)

    def __str__(self):
        return f'{self.Name}'

    class Meta:
        verbose_name = 'Единицы измерения'


# серии
class seriesModel(models.Model):
    Name = models.CharField('Наименование', max_length=10, unique=True, primary_key=True)
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

    Name = models.CharField('Наименование', max_length=50, unique=True, primary_key=True)
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


# номинальный ток
class nominalModel(models.Model):
    Name = models.CharField('Наименование', max_length=10, primary_key=True)

    # название строчки в таблице
    def __str__(self):
        return self.Name

    # название таблицы
    class Meta:
        verbose_name = 'Номинал'


# количество проводников
class conductorsModel(models.Model):
    Name = models.CharField('Наименование', max_length=10)
    quantity = models.CharField('Количество проводников', max_length=1, primary_key=True)

    # название строчки в таблице
    def __str__(self):
        return self.quantity

    # название таблицы
    class Meta:
        verbose_name = 'Количество проводников'


# Название номенклатуры
class NameNomenclature(models.Model):
    CATEGORIES = (
        ('1', 'секции'),
        ('2', 'комплектующие'),
        ('3', 'НКУ')
    )
    # Обозначение: только заглавные латинские буквы, не более 3 символов
    Numbers = models.CharField('Обозначение',
                              max_length=10,
                              validators=[RegexValidator(
                                  regex=r'^[A-Z]{1,10}$',
                                  message='Обозначение должно содержать только заглавные латинские '
                                          'буквы (A-Z) и не более 10 символов')],
                              help_text='Только заглавные латинские буквы, '
                                        'не более 3 символов (например: I, LV, KLF)',
                              primary_key=True)
    Name = models.CharField('Наименование', max_length=100)  # Увеличил до 100 для полных наименований
    unit = models.ForeignKey(UnitModel, on_delete=models.CASCADE, verbose_name='Ед. изм.',
                             null=True, blank=True)
    category = models.CharField('Категория', max_length=100, choices=CATEGORIES)
    # название строчки в таблице
    def __str__(self):
        return self.Name

    class Meta:
        verbose_name = 'Наименование и обозначение номенклатуры'
        verbose_name_plural = 'Наименования и обозначения номенклатуры'
        ordering = ['Name']


# список заказов пока (не задействован)
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


# список расчетов
class MaterialCalculationModel(models.Model):
    series = models.ForeignKey(seriesModel,
                               on_delete=models.CASCADE,
                               to_field='Name',
                               verbose_name="Серия шинопровода")
    conductor_material = models.ForeignKey(materialModel,
                                           on_delete=models.CASCADE,
                                           to_field='Name',
                                           verbose_name="Материал проводника")
    nominal_current = models.ForeignKey(nominalModel,
                                        on_delete=models.CASCADE,
                                        to_field='Name',
                                        verbose_name="Номинальный ток (А)")
    number_of_conductors = models.ForeignKey(conductorsModel,
                                             on_delete=models.CASCADE,
                                             to_field='quantity',
                                             verbose_name="Количество проводников")
    track_length = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Длина трассы (м)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    Responsible = models.CharField('Ответственный', max_length=100)

    def __str__(self):
        return f'{self.series.Name} - {self.conductor_material.Name} ({self.nominal_current.Name} А)'

    class Meta:
        verbose_name = 'Расчет материалов'


# список рабочих ведомостей (не задействован)
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


# Номенклатура
class ComponentsModel(models.Model):

    Numbers = models.CharField('Номер', max_length=30, primary_key=True)
    Name = models.ForeignKey(NameNomenclature,
                             on_delete=models.CASCADE,
                             verbose_name='Наименование',
                             null=True, blank=True)
    price = MoneyField('Цена без НДС',
                       max_digits=10,
                       decimal_places=2,
                       default_currency='RUB',
                       null=True)
    file = models.FileField(null=True, blank=True)
    weight = models.DecimalField('Масса', max_digits=5, decimal_places=2, null=True, blank=True)

    A = models.CharField('Длина', max_length=100, null=True, blank=True)
    B = models.CharField('Длина', max_length=100, null=True, blank=True)
    C = models.CharField('Длина', max_length=100, null=True, blank=True)
    Length = models.DecimalField('Длина', max_digits=10, decimal_places=2, null=True, blank=True)
    series = models.ForeignKey(seriesModel, on_delete=models.CASCADE, verbose_name='Серия',
                               null=True, blank=True)
    conductor_material = models.ForeignKey(materialModel,
                                           on_delete=models.CASCADE,
                                           verbose_name='Материал проводника',
                                           null=True, blank=True)
    number_of_conductors = models.ForeignKey(conductorsModel,
                                             on_delete=models.CASCADE,
                                             verbose_name='Количество проводников',
                                             null=True, blank=True)
    rated_current = models.ForeignKey(nominalModel,
                                      on_delete=models.CASCADE,
                                      verbose_name='Номинальный ток',
                                      null=True, blank=True)

    def __str__(self):
        return f'{self.Name.Name if self.Name else "Без имени"} - {self.Numbers}'

    class Meta:
        verbose_name = 'Номенклатура'


# спецификация сделки
class Specification(models.Model):
    transaction = models.ForeignKey('reg.regModel',
                                    on_delete=models.CASCADE,
                                    verbose_name='Сделка',
                                    related_name='specifications')
    article = models.ForeignKey('ComponentsModel',
                               on_delete=models.CASCADE,
                               verbose_name='Артикул',
                               to_field='Numbers')
    line = models.CharField('Линия', max_length=100, null=True, blank=True)
    quantity = models.IntegerField('Количество', null=True, blank=True)

    def __str__(self):
        return f'Спецификация для {self.transaction.Name}'

    class Meta:
        verbose_name = 'Спецификация'
        verbose_name_plural = 'Спецификации'
