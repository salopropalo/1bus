from django import forms
from .models import (order_registerModel, MaterialCalculationModel, ProcessingOfShopSheetModel,
                     seriesModel, materialModel, nominalModel, conductorsModel, ComponentsModel, MaterialCalculationModel)
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

class calculation_of_materialsForm(ModelForm):
    class Meta:
        model = MaterialCalculationModel
        fields = ['series', 'conductor_material', 'number_of_conductors', 'nominal_current', 'track_length']
        widgets = {
            'series': Select(attrs={'class': 'form-control'}),
            'conductor_material': Select(attrs={'class': 'form-control'}),
            'number_of_conductors': Select(attrs={'class': 'form-control', 'placeholder': 'Номер заказа'}),
            'nominal_current': Select(attrs={'class': 'form-control'}),
            'track_length': TextInput(attrs={'class': 'form-control-file'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class ProcessingOfShopSheetForm(ModelForm):
    class Meta:
        model = ProcessingOfShopSheetModel
        fields = ['nomer_proekta', 'naimenovanie_proekta', 'nomer_zakaza', 'nomer_etapa', 'proizvodstvo', 'file']
        widgets = {
            'nomer_proekta': TextInput(attrs={'class': 'form-control', 'placeholder': 'Только цифры'}),
            'naimenovanie_proekta': TextInput(attrs={'class': 'form-control', 'placeholder': 'Как можно меньше букв'}),
            'nomer_zakaza': TextInput(attrs={'class': 'form-control', 'placeholder': '0000'}),
            'nomer_etapa': TextInput(attrs={'class': 'form-control', 'placeholder': '00'}),
            'proizvodstvo': Select(attrs={'class': 'form-control'}),
            'file': FileInput(attrs={'class': 'form-control-file'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SpecificationFilterForm(forms.Form):
    series = forms.ModelChoiceField(
        queryset=seriesModel.objects.all(),
        label='Серия',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_series'})
    )

    conductor_material = forms.ModelChoiceField(
        queryset=materialModel.objects.all(),
        label='Материал проводника',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_conductor_material'})
    )

    number_of_conductors = forms.ModelChoiceField(
        queryset=conductorsModel.objects.all(),
        label='Количество проводников',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_number_of_conductors'})
    )

    rated_current = forms.ModelChoiceField(
        queryset=nominalModel.objects.all(),
        label='Номинальный ток',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_rated_current'})
    )


class MaterialCalculationForm(forms.ModelForm):
    class Meta:
        model = MaterialCalculationModel
        fields = ['series', 'conductor_material', 'nominal_current', 'number_of_conductors', 'track_length',
                  'Responsible']
        widgets = {
            'series': forms.Select(attrs={'class': 'form-select'}),
            'conductor_material': forms.Select(attrs={'class': 'form-select'}),
            'nominal_current': forms.Select(attrs={'class': 'form-select'}),
            'number_of_conductors': forms.Select(attrs={'class': 'form-select'}),
            'track_length': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'Responsible': forms.TextInput(attrs={'class': 'form-control'}),
        }