from django import forms
from .models import order_registerModel
from django.forms import ModelForm, TextInput, Select, FileInput

class order_registerForm(ModelForm):
    class Meta:
        model = order_registerModel
        fields = ['nomer_proekta', 'naimenovanie_proekta', 'nomer_zakaza', 'proizvodstvo', 'file']
        widgets = {
            'nomer_proekta': TextInput(attrs={'class': 'form-control', 'placeholder': 'Номер проекта'}),
            'naimenovanie_proekta': TextInput(attrs={'class': 'form-control', 'placeholder': 'Наименование проекта'}),
            'nomer_zakaza': TextInput(attrs={'class': 'form-control', 'placeholder': 'Номер заказа'}),
            'proizvodstvo': Select(attrs={'class': 'form-control'}),
            'file': FileInput(attrs={'class': 'form-control-file'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
