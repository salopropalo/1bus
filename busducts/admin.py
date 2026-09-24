from django.contrib import admin
from .models import BusductType, InfoBlock

@admin.register(BusductType)
class BusductTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(InfoBlock)
class InfoBlockAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')
    list_editable = ('order', 'is_active')