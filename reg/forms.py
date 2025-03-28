from .models import regModel, companyModel
from django.forms import ModelForm, TextInput, Select

# форма для списка сделок в модальном окне создания и редактирования новой карточки сделки
class transactionListForm(ModelForm):
    class Meta:
        model = regModel
        fields = ['Name', 'Adres_obj']
        widgets = {
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

# форма для карточки сделка
class transactionForm(ModelForm):
    class Meta:
        model = regModel
        fields = ['Customer_company', 'Seller_company', 'Adres_obj']
        labels = {
            'Customer_company': 'Компания заказчик',
            'Seller_company': 'Компания продавец',
            'Adres_obj': 'Адрес объекта',
        }
        widgets = {
            'Customer_company': Select(attrs={'class': 'form-control'}),
            'Seller_company': Select(attrs={'class': 'form-control'}),
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
