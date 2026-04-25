import tkinter as tk
from tkinter import messagebox
import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import numpy as np

# Коэффициенты линейного расширения (1/°C)
coefficients = {
    "медь": 16.5e-6,
    "алюминий": 23.1e-6  # Точное значение, как ты использовал
}

# Модули Юнга (Па)
E_moduli = {
    "медь": 110e9,
    "алюминий": 70e9
}

def рассчитать_и_показать():
    try:
        material = var_material.get().lower()
        L0 = float(entry_length.get())
        T1 = float(entry_T1.get())
        T2 = float(entry_T2.get())

        if material not in coefficients:
            raise ValueError("Выберите 'медь' или 'алюминий'.")

        alpha = coefficients[material]
        delta_T = T2 - T1
        temps = np.linspace(T1, T2, 100)
        delta_L = L0 * alpha * (temps - T1)
        lengths = L0 + delta_L

        final_length = lengths[-1]
        elongation = final_length - L0

        # Напряжение (при жёстком закреплении концов)
        E = E_moduli.get(material)
        stress = E * alpha * delta_T  # в Па

        info = (
            f"Материал: {material.capitalize()}\n"
            f"Начальная длина: {L0:.3f} м\n"
            f"Температурный диапазон: от {T1} до {T2} °C\n"
            f"Коэффициент расширения: {alpha:.2e} 1/°C\n"
            f"Удлинение: {elongation:.6f} м ≈ {elongation * 1000:.2f} мм\n"
            f"Конечная длина: {final_length:.6f} м\n"
            f"Температурное напряжение: {stress / 1e6:.2f} МПа"
        )

        messagebox.showinfo("Результаты расчёта", info)

        plt.figure(figsize=(6, 4))
        plt.plot(temps, lengths, label=material.capitalize(), color='blue')
        plt.xlabel("Температура (°C)")
        plt.ylabel("Длина проводника (м)")
        plt.title("Удлинение проводника при нагреве")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig("расширение_график.png")
        plt.show()

    except Exception as e:
        messagebox.showerror("Ошибка", str(e))

# GUI интерфейс
root = tk.Tk()
root.title("Расчёт теплового расширения проводника")

tk.Label(root, text="Материал:").grid(row=0, column=0, sticky="w")
var_material = tk.StringVar(value="алюминий")
tk.OptionMenu(root, var_material, "медь", "алюминий").grid(row=0, column=1)

tk.Label(root, text="Начальная длина (м):").grid(row=1, column=0, sticky="w")
entry_length = tk.Entry(root)
entry_length.insert(0, "17.0")
entry_length.grid(row=1, column=1)

tk.Label(root, text="Температура от (°C):").grid(row=2, column=0, sticky="w")
entry_T1 = tk.Entry(root)
entry_T1.insert(0, "0")
entry_T1.grid(row=2, column=1)

tk.Label(root, text="Температура до (°C):").grid(row=3, column=0, sticky="w")
entry_T2 = tk.Entry(root)
entry_T2.insert(0, "36")
entry_T2.grid(row=3, column=1)

tk.Button(root, text="Рассчитать", command=рассчитать_и_показать).grid(row=4, column=0, columnspan=2, pady=10)

root.mainloop()