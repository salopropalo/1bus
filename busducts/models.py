from django.db import models
from django.utils.text import slugify

class BusductType(models.Model):
    """Типы шинопроводов: шинный мост, магистральный, распределительный"""
    name = models.CharField(max_length=100, verbose_name='Название')
    slug = models.SlugField(unique=True, blank=True, verbose_name='Слаг')
    short_description = models.TextField(verbose_name='Краткое описание')
    full_description = models.TextField(blank=True, verbose_name='Полное описание (страница)')
    image = models.ImageField(upload_to='busducts/types/', blank=True, null=True, verbose_name='Изображение')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    is_active = models.BooleanField(default=True, verbose_name='Активно')

    class Meta:
        ordering = ['order']
        verbose_name = 'Тип шинопровода'
        verbose_name_plural = 'Типы шинопроводов'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class InfoBlock(models.Model):
    """Информационные блоки для второй части страницы (каталог, преимущества, сертификаты и т.д.)"""
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Текст')
    image = models.ImageField(upload_to='busducts/info/', verbose_name='Изображение')
    link = models.URLField(blank=True, null=True, verbose_name='Ссылка (опционально)')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    is_active = models.BooleanField(default=True, verbose_name='Активно')

    class Meta:
        ordering = ['order']
        verbose_name = 'Информационный блок'
        verbose_name_plural = 'Информационные блоки'

    def __str__(self):
        return self.title