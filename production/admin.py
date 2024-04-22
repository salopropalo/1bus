from django.contrib import admin
from .models import seriesModel, materialModel, nominalModel, conductorsModel
#регистрация таблиц из баз данных
# Register your models here.

#Добавляем таблицу из models.py
admin.site.register(seriesModel)
admin.site.register(materialModel)
admin.site.register(nominalModel)
admin.site.register(conductorsModel)