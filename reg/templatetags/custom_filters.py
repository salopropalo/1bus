from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Возвращает значение словаря по ключу, либо 0."""
    if dictionary is None:
        return 0
    return dictionary.get(key, 0)

@register.filter
def mm_to_m(value):
    """Переводит миллиметры в метры (деление на 1000)."""
    try:
        return Decimal(str(value)) / 1000
    except (ValueError, TypeError):
        return Decimal('0')

@register.filter
def thousands_space(value):
    """Форматирует число с пробелом как разделителем тысяч и запятой для дробной части."""
    try:
        # Приводим к Decimal для точности
        d = Decimal(str(value))
        # Форматируем с разделителями: целая часть - пробелы, дробная - 2 знака
        # Используем функцию format
        formatted = f'{d:,.2f}'  # даёт запятые как разделители тысяч и точку для дробной части
        # Заменяем запятые на пробелы, а точки на запятые (для российского формата)
        formatted = formatted.replace(',', ' ').replace('.', ',')
        return formatted
    except (ValueError, TypeError):
        return '0,00'