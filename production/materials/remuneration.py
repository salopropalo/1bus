from decimal import Decimal, ROUND_HALF_UP

def to_decimal(s):
    return Decimal(s.strip())

def money(d: Decimal) -> Decimal:
    """Округление до копеек (для вывода и расчётов выплат)"""
    return d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def round_rubles(d: Decimal) -> int:
    """Округление до целых рублей (НДФЛ)"""
    return int(d.quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def main():
    # Ввод данных
    salary = to_decimal(input("Введите сумму оклада (руб.): "))
    ndfl_pct = to_decimal(input("Введите процент НДФЛ (%): "))
    days_in_month = int(input("Введите количество рабочих дней в месяце: "))
    days_first = int(input("Введите количество рабочих дней в первой половине месяца: "))

    # Проверка корректности
    if days_first > days_in_month or days_first < 0 or days_in_month <= 0:
        print("Ошибка: проверьте количество дней.")
        return

    # Дневная ставка
    daily = salary / Decimal(days_in_month)

    # Начисления
    accrual_first = money(daily * Decimal(days_first))
    accrual_second = money(salary - accrual_first)

    # НДФЛ по частям (округляем до рублей)
    ndfl_first = round_rubles(accrual_first * ndfl_pct / Decimal(100))
    ndfl_second = round_rubles(accrual_second * ndfl_pct / Decimal(100))

    # Выплаты на руки
    payout_first = money(accrual_first - Decimal(ndfl_first))
    payout_second = money(accrual_second - Decimal(ndfl_second))

    # Итоги
    total_ndfl = ndfl_first + ndfl_second
    total_net = money(payout_first + payout_second)

    # Вывод
    print("\n--- Результат ---")
    print(f"Начислено (первая половина): {accrual_first:.2f} руб.")
    print(f"Начислено (вторая половина): {accrual_second:.2f} руб.")
    print(f"НДФЛ (первая половина): {ndfl_first} руб.")
    print(f"НДФЛ (вторая половина): {ndfl_second} руб.")
    print(f"Выплата (первая половина): {payout_first:.2f} руб.")
    print(f"Выплата (вторая половина): {payout_second:.2f} руб.")
    print(f"НДФЛ всего: {total_ndfl} руб.")
    print(f"Итого на руки за месяц: {total_net:.2f} руб.")

if __name__ == "__main__":
    main()