from django.db import models
from django.core.validators import RegexValidator


class Stat(models.Model):
    STATUS = (
        ('1', 'создан'),
        ('2', 'согласован'),
        ('3', 'в работе'),
        ('4', 'завершён')
    )

class regModel(models.Model):
    numbers = models.CharField('Номер проекта', max_length=10)
    NameProg = models.CharField('Наименование', max_length=100)
    Date_born = models.DateField('Дата создания', auto_now=True)
    Responsible = models.CharField('Ответственный', max_length=100)
    Customer_company = models.CharField('', max_length=50)
    Adres_obj = models.TextField('Адрес объекта')
    Status = models.CharField('Статус', max_length=30, default='создан', choices=Stat.STATUS)

    # название строчки в таблице
    def __str__(self):
        return 'Проект №' + self.numbers + ' ' + self.NameProg

    # название таблицы
    class Meta:
        verbose_name = 'Таблица регистрации'

# модель для создания компании
class companyModel(models.Model):
    class Stat(models.Model):
        STATUS = (
            ('1', 'действующая компания'),
            ('2', 'ликвидирована'),
        )

    Name = models.CharField('Имя', max_length=255)
    Nmae_Company = models.TextField('Наименование', max_length=255)
    Full_Nmae_Company = models.CharField('Полное наименование', max_length=255)
    inn_validator = RegexValidator(regex=r'^\d{9}$',
                                   message="ИНН должен содержать только цифры и быть длиной 10 символов")
    INN = models.CharField('ИНН', max_length=9, validators=[inn_validator])
    kpp_validator = RegexValidator(regex=r'^\d{9}$',
                                   message="КПП должен содержать только цифры и быть длиной 9 символов")
    KPP = models.CharField('КПП', max_length=9, validators=[kpp_validator])
    Legal_address = models.CharField('Юридический адрес', max_length=255)
    Actual_address = models.CharField('Фактический адрес', max_length=255)
    OGRN = models.CharField('ОГРН', max_length=10)
    OKPO = models.CharField('ОКПО', max_length=10)
    Checking_account_validator = RegexValidator(regex=r'^\d{20}$',
                                                message="Расчетный счёт должен содержать только "
                                                        "цифры и быть длиной 20 символов")
    Checking_account = models.CharField('Расчетный счёт', max_length=20, validators=[Checking_account_validator])
    Correspondent_account_validator = RegexValidator(regex=r'^\d{20}$',
                                                     message="Расчетный счёт должен содержать "
                                                             "только цифры и быть длиной 20 символов")
    Correspondent_account = models.CharField('Корреспондентский счет', max_length=20,
                                             validators=[Correspondent_account_validator])
    BIK_validator = RegexValidator(regex=r'^\d{9}$',
                                   message="БИК должен содержать только цифры и быть длиной 9 символов")
    BIK = models.CharField('БИК', max_length=9, validators=[BIK_validator])
    Bank = models.CharField('Банк', max_length=255)
    Name_manager = models.CharField('Должность руководителя', max_length=255)
    Manager = models.CharField('ФИО руководителя', max_length=255)
    Right_of_management = models.CharField('Основание управления', max_length=255)
    Telephone_validator = RegexValidator(regex=r'^\d{11}$',
                                         message="Номер телефона должен "
                                                 "содержать только цифры и быть длиной 11 символов")
    Telephone = models.CharField('Номер телефона', max_length=11, validators=[Telephone_validator])
    Date_born = models.DateField('Дата создания', auto_now=True)
    Responsible = models.CharField('Ответственный', max_length=100)
    Status = models.CharField('Статус', max_length=255, default='действующая компания', choices=Stat.STATUS)

    # название строчки в таблице
    def __str__(self):
        return self.Name

    # название таблицы
    class Meta:
        verbose_name = 'Компании'
