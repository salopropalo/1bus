from django import forms
from .models import order_registerModel, MaterialCalculationModel
from django.forms import ModelForm, TextInput, Select, FileInput

# для комплекта документов
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

# для расчета материалов

# class calculation_of_materialsForm(forms.Form):
#     SERIES_CHOICES = [
#         ('E3', 'E3'),
#         ('CR1', 'CR1'),
#         ('CRM', 'CRM'),
#         ('CRM-C', 'CRM-C'),
#         ('A5', 'A5'),
#     ]
#
#     MATERIAL_CHOICES = [
#         ('CU', 'CU'),
#         ('AL', 'AL'),
#     ]
#
#     NOMINAL_CHOICES = [
#         ('250', '250'),
#         ('400', '400'),
#         ('630', '630'),
#         ('800', '800'),
#         ('1000', '1000'),
#         ('1250', '1250'),
#         ('1600', '1600'),
#         ('2000', '2000'),
#         ('2500', '2500'),
#         ('3200', '3200'),
#         ('4000', '4000'),
#         ('5000', '5000'),
#         ('6400', '6400'),
#     ]
#
#     NOMBER_CHOICES = [
#         ('3', '3'),
#         ('4', '4'),
#         ('5', '5'),
#     ]
#
#     series = forms.ChoiceField(label="Серия шинопровода", choices=SERIES_CHOICES)
#     conductor_material = forms.ChoiceField(label="Материал проводника", choices=MATERIAL_CHOICES)
#     nominal_current = forms.ChoiceField(label="Номинальный ток (А)", choices=NOMINAL_CHOICES)
#     number_of_conductors = forms.ChoiceField(label="Количество проводников", choices=NOMBER_CHOICES)
#     track_length = forms.DecimalField(label="Длина трассы (м)", max_digits=10, decimal_places=2)
class calculation_of_materialsForm(ModelForm):
    class Meta:
        model = MaterialCalculationModel
        fields = ['series', 'conductor_material', 'nominal_current', 'number_of_conductors', 'track_length']
        widgets = {
            'series': Select(attrs={'class': 'form-control'}),
            'conductor_material': Select(attrs={'class': 'form-control'}),
            'number_of_conductors': Select(attrs={'class': 'form-control', 'placeholder': 'Номер заказа'}),
            'nominal_current': Select(attrs={'class': 'form-control'}),
            'track_length': TextInput(attrs={'class': 'form-control-file'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
