from django.db import models
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
        return self.Name

    # название таблицы
    class Meta:
        verbose_name = 'Количество проводников'

