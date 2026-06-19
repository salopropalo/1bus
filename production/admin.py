from django.contrib import admin
from .models import (seriesModel, materialModel, nominalModel, conductorsModel, ComponentsModel, UnitModel,
                     MaterialCalculationModel, NameNomenclature, Specification, PurchaseItem, SupplierPrice)
admin.site.register(UnitModel)

@admin.register(seriesModel)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ['Name', 'Standard', 'Description']
    search_fields = ['Name']

@admin.register(materialModel)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['Name', 'Designation', 'tip', 'Magnetic']
    search_fields = ['Name']

@admin.register(conductorsModel)
class ConductorsAdmin(admin.ModelAdmin):
    list_display = ['Name', 'quantity']
    search_fields = ['Name']

@admin.register(nominalModel)
class NominalAdmin(admin.ModelAdmin):
    list_display = ['Name']
    search_fields = ['Name']

@admin.register(ComponentsModel)
class ComponentsAdmin(admin.ModelAdmin):
    list_display = ['Name', 'Numbers']
    list_filter = ['series__Name', 'conductor_material__Name', 'number_of_conductors__quantity',
                   'rated_current__Name']
    search_fields = ['Name', 'Numbers', 'series', 'conductor_material', 'number_of_conductors', 'rated_current']
    list_per_page = 100  # Количество записей на странице

@admin.register(MaterialCalculationModel)
class MaterialCalculationAdmin(admin.ModelAdmin):
    list_display = ['id', 'series', 'conductor_material', 'nominal_current', 'number_of_conductors', 'track_length', 'created_at', 'Responsible']
    list_filter = ['series', 'conductor_material', 'created_at']
    search_fields = ['Responsible']

@admin.register(NameNomenclature)
class NameNomenclatureAdmin(admin.ModelAdmin):
    list_display = ['Name', 'Numbers', 'category']
    list_filter = ['Name', 'Numbers', 'category']
    search_fields = ['Name']

@admin.register(Specification)
class SpecificationAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'article', 'line', 'quantity']
    search_fields = ['article']
    list_per_page = 100

class SupplierPriceInline(admin.TabularInline):
    model = SupplierPrice
    extra = 1

@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ['article', 'name', 'weight', 'size', 'unit', 'weight_unit', 'category', 'use']
    search_fields = ['article', 'name']
    inlines = [SupplierPriceInline]
