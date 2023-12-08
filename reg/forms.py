from .models import regModel
from django.forms import ModelForm, TextInput

class regForm(ModelForm):
    class Meta:
        model = regModel
        fields = ['NameProg', 'Adres_obj']
        widgets = {
            'NameProg': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите наименование проекта'
                }),
            'Adres_obj': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите адрес объекта (Страна, Город, Улица, №Дома)'
                })
                }

class sdelkaForm(ModelForm):
    class Meta:
        model = regModel
        fields = ['Adres_obj']
        widgets = {
            'Adres_obj': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите адрес объекта (Страна, Город, Улица, №Дома)'
                }),
            'NameProg': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите наименование проекта'
                }),
                }
