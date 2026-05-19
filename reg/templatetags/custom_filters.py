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
        # Убираем пробелы и заменяем запятую на точку (на случай если пришла строка после floatformat)
        cleaned = str(value).strip().replace(' ', '').replace(',', '.')
        d = Decimal(cleaned)
        formatted = f'{d:,.2f}'
        formatted = formatted.replace(',', ' ').replace('.', ',')
        return formatted
    except (ValueError, TypeError, Exception):
        return '0,00'