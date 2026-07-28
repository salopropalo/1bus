from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid


# модель для создания компании
class companyModel(models.Model):

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

    Full_Name_Company = models.CharField('Полное наименование', max_length=255, unique=True)
    inn_validator = RegexValidator(regex=r'^\d{10}$',
                                   message="ИНН должен содержать только цифры и быть длиной 10 символов")
    INN = models.CharField('ИНН', max_length=10, validators=[inn_validator])
    kpp_validator = RegexValidator(regex=r'^\d{9}$',
                                   message="КПП должен содержать только цифры и быть длиной 9 символов")
    KPP = models.CharField('КПП', max_length=9, validators=[kpp_validator])
    Legal_address = models.CharField('Юридический адрес', max_length=255)
    Actual_address = models.CharField('Фактический адрес', max_length=255)
    OGRN = models.CharField('ОГРН', max_length=13)
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

    # название строчки в таблице
    def __str__(self):
        return self.Name

    # название таблицы
    class Meta:
        verbose_name = 'Компании'


# модели для сделок
class regModel(models.Model):

    # ------ эти поля должны быть обязательны для любого документа или списка ------------------------------------------
    STATUS = (
        ('1', 'создан'),
        ('2', 'согласован'),
        ('3', 'в работе'),
        ('4', 'завершён'),
        ('5', 'отменен')
    )   # Статус может быть создан до 5 пунктов

    DELIVERY_TERMS = (
        ('3-4', '3-4 недели'),
        ('4-6', '4-6 недель'),
        ('6-8', '6-8 недель'),
        ('8-12', '8-12 недель'),
        ('12-16', '12-16 недель'),
        ('20', '20 недель'),
    )

    DELIVERY_CHOICES = (
        ('self', 'Самовывоз'),
        ('delivery', 'Доставка'),
    )

    GUARANTEE_CHOICES = (
        ('12', '12 месяцев'),
        ('24', '24 месяца'),
        ('36', '36 месяцев'),
        ('60', '60 месяцев'),
    )

    Numbers = models.CharField('Номер', max_length=10)
    Name = models.CharField('Наименование', max_length=100)
    Date_born = models.DateField('Дата создания', #auto_now=True,
                                 default=timezone.now,  # Устанавливает текущую дату при создании
                                 editable=False        # Делает поле неизменяемым в формах и админке
                                 )
    Responsible = models.CharField('Ответственный', max_length=100)
    Status = models.CharField('Статус', max_length=30, default='1', choices=STATUS)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    # -----------------------------------------------------------------------------------------------------------------

    Customer_company = models.ForeignKey(companyModel,
                                         on_delete=models.CASCADE,
                                         to_field='Name',
                                         related_name='customer_company',
                                         blank=True,  # Делаем поле необязательным
                                         null=True  # Добавляем null=True для обозначения пустого значения в базе данных
                                         )
    Seller_company = models.ForeignKey(companyModel,
                                       on_delete=models.CASCADE,
                                       to_field='Name',
                                       related_name='seller_company',
                                       blank=True,  # Делаем поле необязательным
                                       null=True  # Добавляем null=True для обозначения пустого значения в базе данных
                                       )
    #List_of_products = models.
    Adres_obj = models.TextField('Адрес объекта')

    # Скидка
    sales = models.DecimalField(
        'Скидка',
        max_digits=10,
        decimal_places=3,
        default=0,
        blank=True,
        null=True
    )
    delivery_term = models.CharField('Срок поставки', max_length=10, choices=DELIVERY_TERMS, default='4-6', null=True,
                                     blank=True)
    payment_terms = models.TextField('Условия оплаты', null=True, blank=True,
                                     default='40% аванс, 40% перед отгрузкой, 20% отсрочка после отгрузки не более 10 дней')
    delivery_type = models.CharField('Тип доставки', max_length=10, choices=DELIVERY_CHOICES, default='delivery',
                                     null=True, blank=True)
    guarantee = models.CharField('Гарантия', max_length=5, choices=GUARANTEE_CHOICES, default='24', null=True,
                                 blank=True)

    # название строчки в таблице
    def __str__(self):
        return f'Проект №{self.Numbers} {self.Name} - {self.get_Status_display()}'

    # название таблицы
    class Meta:
        verbose_name = 'Таблица регистрации'