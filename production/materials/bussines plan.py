from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import datetime
import os


def register_fonts():
    """Регистрируем шрифты с поддержкой кириллицы"""
    try:
        # Попробуем использовать DejaVu Sans - обычно есть в системах
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
        return 'DejaVuSans'
    except:
        # Если DejaVu нет, попробуем Arial Unicode MS (для Windows)
        try:
            pdfmetrics.registerFont(TTFont('ArialUnicode', 'arialuni.ttf'))
            return 'ArialUnicode'
        except:
            # Если ничего не найдено, используем стандартный шрифт
            return 'Helvetica'


def create_investment_proposal(
        investment_amount=15000000,  # Сумма инвестиций в рублях
        return_period=24,  # Срок возврата инвестиций в месяцах
        annual_interest=8,  # Годовая процентная ставка по дивидендам (%)
        investor_share=50,  # Доля инвестора в уставном капитале (%)
        final_share=15,  # Доля инвестора после возврата инвестиций (%)
        filename="investment_proposal.pdf"
):
    """
    Создает PDF-документ с инвестиционным предложением.

    Параметры:
    investment_amount - общая сумма инвестиций (руб)
    return_period - срок возврата инвестиций (мес)
    annual_interest - годовая ставка по дивидендам (%)
    investor_share - начальная доля инвестора (%)
    final_share - доля инвестора после возврата (%)
    filename - имя выходного файла
    """

    # Регистрируем шрифты
    font_name = register_fonts()
    bold_font = f'{font_name}-Bold' if font_name != 'Helvetica' else 'Helvetica-Bold'

    # Расчеты
    monthly_return = investment_amount / return_period  # Ежемесячный возврат
    yearly_return = investment_amount / (return_period / 12)  # Годовой возврат
    dividend_year1 = investment_amount * (annual_interest / 100)  # Дивиденды 1 год
    dividend_year2 = (investment_amount - yearly_return) * (annual_interest / 100)  # Дивиденды 2 год
    total_dividends = dividend_year1 + dividend_year2  # Общая сумма дивидендов
    returned_share = investor_share - final_share  # Доля, возвращаемая инвестором

    # Создаем стили с нужными шрифтами
    styles = getSampleStyleSheet()

    # Основной стиль текста с переносами
    if 'NormalCustom' not in styles:
        styles.add(ParagraphStyle(
            name='NormalCustom',
            fontName=font_name,
            fontSize=9,
            leading=11,
            spaceBefore=6,
            spaceAfter=6
        ))

    # Стиль заголовков
    if 'HeadingCustom' not in styles:
        styles.add(ParagraphStyle(
            name='HeadingCustom',
            fontName=bold_font,
            fontSize=12,
            leading=14,
            spaceAfter=12,
            textColor=colors.HexColor('#11557C')
        ))

    # Стиль заголовка документа
    if 'TitleCustom' not in styles:
        styles.add(ParagraphStyle(
            name='TitleCustom',
            fontName=bold_font,
            fontSize=14,
            leading=16,
            alignment=1,  # CENTER
            spaceAfter=12,
            textColor=colors.HexColor('#0B3D5F')
        ))

    # Функция для создания параграфов с переносами
    def wrap_text(text, width=100):
        return Paragraph(text.replace('\n', '<br/>'), styles['NormalCustom'])

    # Данные для таблиц с переносами текста
    investor_terms = [
        ["№", "Параметр", "Условия для инвестора", "Комментарий"],
        ["1", wrap_text("Сумма инвестиций"),
         wrap_text(f"{investment_amount:,.0f} ₽".replace(",", " ")),
         wrap_text("Полное финансирование проекта")],
        ["2", wrap_text("Форма участия"),
         wrap_text(f"{investor_share}% в уставном капитале"),
         wrap_text("Временное владение долей")],
        ["3", wrap_text("Возврат инвестиций"),
         wrap_text(
             f"Равными частями в течение {return_period} месяцев\n({monthly_return:,.0f} ₽/мес)".replace(",", " ")),
         wrap_text("Без процентов, только тело инвестиций")],
        ["4", wrap_text("Доходность (дивиденды)"),
         wrap_text(f"Ежегодные выплаты по ставке {annual_interest}% годовых"),
         wrap_text("Начисляется на остаток невозвращенной суммы")],
        ["5", wrap_text("Финалный расчёт"),
         wrap_text(f"Инвестор возвращает {returned_share}% доли,\nсохраняя {final_share}%"),
         wrap_text("Условие: все выплаты выполнены в срок")],
        ["6", wrap_text("Итоговый доход"),
         wrap_text(f"~{total_dividends:,.0f} ₽ дивидендов + {final_share}% доли".replace(",", " ")),
         wrap_text("Суммарная выгода за весь период")]
    ]

    payment_schedule = [
        [wrap_text(x) for x in
         ["Год", "Остаток инвестиций", f"Дивиденды ({annual_interest}%)", "Возврат тела", "Итого выплат",
          "Доля инвестора"]],
        [wrap_text("1"),
         wrap_text(f"{investment_amount:,.0f} ₽".replace(",", " ")),
         wrap_text(f"{dividend_year1:,.0f} ₽".replace(",", " ")),
         wrap_text(f"{yearly_return:,.0f} ₽".replace(",", " ")),
         wrap_text(f"{dividend_year1 + yearly_return:,.0f} ₽".replace(",", " ")),
         wrap_text(f"{investor_share}%")],
        [wrap_text("2"),
         wrap_text(f"{investment_amount - yearly_return:,.0f} ₽".replace(",", " ")),
         wrap_text(f"{dividend_year2:,.0f} ₽".replace(",", " ")),
         wrap_text(f"{yearly_return:,.0f} ₽".replace(",", " ")),
         wrap_text(f"{dividend_year2 + yearly_return:,.0f} ₽".replace(",", " ")),
         wrap_text(f"{investor_share}%")],
        [wrap_text("3"),
         wrap_text("0 ₽"),
         wrap_text("0 ₽"),
         wrap_text("0 ₽"),
         wrap_text("Дивиденды за долю"),
         wrap_text(f"{final_share}%")]
    ]

    # Создание PDF с увеличенными полями
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)
    story = []

    # Заголовок
    title = Paragraph("ИНВЕСТИЦИОННОЕ ПРЕДЛОЖЕНИЕ", styles['TitleCustom'])
    story.append(title)

    # Дата генерации
    date_str = Paragraph(
        f"Дата: {datetime.datetime.now().strftime('%d.%m.%Y')}",
        styles['NormalCustom']
    )
    story.append(date_str)
    story.append(Spacer(1, 24))

    # Основные условия
    story.append(Paragraph("УСЛОВИЯ ДЛЯ ИНВЕСТОРА", styles['HeadingCustom']))

    # Ширина столбцов с учетом переносов
    col_widths = [25, 80, 120, 150]

    investor_table = Table(investor_terms, colWidths=col_widths, repeatRows=1)
    investor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F81BD')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), bold_font),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#DCE6F1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), True)  # Включаем перенос слов
    ]))
    story.append(investor_table)
    story.append(Spacer(1, 24))

    # График выплат
    story.append(Paragraph("ГРАФИК ВЫПЛАТ", styles['HeadingCustom']))

    # Ширина столбцов для графика выплат
    payment_col_widths = [30, 70, 70, 70, 70, 50]

    payment_table = Table(payment_schedule, colWidths=payment_col_widths, repeatRows=1)
    payment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F81BD')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), bold_font),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#DCE6F1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), True)  # Включаем перенос слов
    ]))
    story.append(payment_table)
    story.append(Spacer(1, 24))

    # Итоговый расчёт
    story.append(Paragraph("ИТОГОВАЯ ДОХОДНОСТЬ", styles['HeadingCustom']))

    total_return = [
        Paragraph(f"• Возврат инвестиций: <b>{investment_amount:,.0f} ₽</b>", styles['NormalCustom']),
        Paragraph(f"• Дивиденды за 2 года: <b>{total_dividends:,.0f} ₽</b>", styles['NormalCustom']),
        Paragraph(f"• Сохранённая доля в бизнесе: <b>{final_share}%</b>", styles['NormalCustom']),
        Paragraph(f"• Общая доходность за период: <b>{(total_dividends / investment_amount) * 100:.1f}%</b>",
                  styles['NormalCustom']),
        Spacer(1, 12),
        Paragraph(f"<i>Примечание: расчеты приведены для ставки {annual_interest}% годовых.</i>",
                  styles['NormalCustom'])
    ]
    story.extend(total_return)

    doc.build(story)
    print(f"Файл '{filename}' успешно создан!")
    print(f"Использован шрифт: {font_name}")


# Пример использования с комментариями параметров
create_investment_proposal(
    investment_amount=15000000,  # 15 млн рублей инвестиций
    return_period=24,  # Возврат за 24 месяца (2 года)
    annual_interest=8,  # 8% годовых по дивидендам
    investor_share=50,  # 50% начальная доля инвестора
    final_share=15,  # 15% сохраняется после возврата
    filename="инвест_предложение.pdf"
)