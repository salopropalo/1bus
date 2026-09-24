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

@register.filter
def initials(name):

    if not name:
        return ""

    parts = name.split()

    if len(parts) == 3:
        return f"{parts[0]} {parts[1][0]}. {parts[2][0]}."

    return name

@register.filter
def phone(value):
    if not value:
        return ""

    value = "".join(filter(str.isdigit, str(value)))

    if len(value) == 11:
        return f"+7 ({value[1:4]}) {value[4:7]}-{value[7:9]}-{value[9:11]}"

    return value