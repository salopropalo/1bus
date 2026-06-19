from .models import regModel, companyModel
from django.forms import ModelForm, TextInput, Select
from django.forms.widgets import Select, Textarea, NumberInput

# форма для списка сделок в модальном окне создания и редактирования новой карточки сделки
class transactionListForm(ModelForm):
    class Meta:
        model = regModel
        fields = ['Numbers', 'Name', 'Adres_obj']
        widgets = {
            'Numbers': TextInput(attrs={'class': 'form-control'}),
            'Name': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите наименование проекта'
                }),
            'Adres_obj': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите адрес объекта (Страна, Город, Улица, №Дома)'
                }),
            'Customer_company': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Выберите компанию заказчика'
            }),
            'Seller_company': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Выберите компанию поставщика'
            })
                }

class transactionForm(ModelForm):
    class Meta:
        model = regModel
        fields = [
            'Customer_company',
            'Seller_company',
            'Adres_obj',
            'sales',
            'delivery_type',
            'guarantee',
            'payment_terms',
            'delivery_term',
        ]
        labels = {
            'Status': 'Статус',
            'Customer_company': 'Компания заказчик',
            'Seller_company': 'Компания покупатель',
            'Adres_obj': 'Адрес объекта',
            'sales': 'Скидка (%)',
            'delivery_type': 'Тип доставки',
            'guarantee': 'Гарантия',
            'payment_terms': 'Условия оплаты',
            'delivery_term': 'Срок поставки',
        }
        widgets = {
            'Status': Select(attrs={'class': 'form-control'}),
            'Customer_company': Select(attrs={'class': 'form-control'}),
            'Seller_company': Select(attrs={'class': 'form-control'}),
            'Adres_obj': Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'sales': NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 99}),
            'delivery_type': Select(attrs={'class': 'form-control'}),
            'guarantee': Select(attrs={'class': 'form-control'}),
            'payment_terms': Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'delivery_term': Select(attrs={'class': 'form-control'}),
        }

# форма для карточки компании
class companyForm(ModelForm):
    class Meta:
        model = companyModel
        fields = ['Name', 'Full_Name_Company', 'INN', 'KPP', 'Legal_address', 'Actual_address',
                  'OGRN', 'OKPO', 'Checking_account', 'Correspondent_account', 'BIK', 'Bank', 'Name_manager',
                  'Manager', 'Right_of_management', 'Telephone']
        widgets = {
                    'Name': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'Наименование'
                            }),
                    'Full_Name_Company': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'Полное наименование'
                            }),
                    'INN': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'ИНН'
                            }),
                    'KPP': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'КПП'
                            }),
                    'Legal_address': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'Юридический адрес'
                            }),
                    'Actual_address': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'Фактический адрес'
                            }),
                    'OGRN': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'ОГРН'
                            }),
                    'OKPO': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'ОКПО'
                            }),
                    'Checking_account': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'Расчетный счёт'
                            }),
                    'Correspondent_account': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'Корреспондентский счет'
                            }),
                    'BIK': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'БИК'
                            }),
                    'Bank': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'Банк'
                            }),
                    'Name_manager': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'Должность руководителя'
                            }),
                    'Manager': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'ФИО руководителя'
                            }),
                    'Right_of_management': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'Основание управления'
                            }),
                    'Telephone': TextInput(attrs={
                            'class': 'form-control',
                            'placeholder': 'Номер телефона'
                            })
                }

