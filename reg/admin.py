from django.contrib import admin
from .models import regModel, companyModel

@admin.register(regModel)
class regModelAdmin(admin.ModelAdmin):
    list_display = ['Numbers', 'Name', 'Responsible', 'Status', 'Customer_company', 'Date_born']
    list_filter = ['Status', 'delivery_type', 'guarantee', 'delivery_term']
    search_fields = ['Numbers', 'Name', 'Responsible']
    fields = [
        'Numbers',
        'Name',
        'Responsible',
        'Status',
        'Customer_company',
        'Seller_company',
        'Adres_obj',
        'sales',
        'delivery_term',
        'payment_terms',
        'delivery_type',
        'guarantee',
    ]

admin.site.register(companyModel)