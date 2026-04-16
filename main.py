# Модель: Математичне моделювання оптимального розкрою рулонної тканини для виробництва футболок
# Автор: Жарук Данил, Холудієв Денис, група АІ-235

#!pip install pulp matplotlib

import os
import random
from pulp import LpProblem, LpVariable, LpMinimize, LpInteger, value
import matplotlib
matplotlib.use('Agg')  # для роботи без дисплею (Docker)
import matplotlib.pyplot as plt
from itertools import combinations_with_replacement

# 🔹 Змінні середовища (додано для Docker / ЛР2)
STUDENT_NAME = os.environ.get("STUDENT_NAME", "Жарук Данил, Холудієв Денис")
GROUP        = os.environ.get("GROUP", "АІ-235")
MODE         = os.environ.get("MODE", "eco")

print("=" * 50)
print(f"👤 Студент : {STUDENT_NAME}")
print(f"🎓 Група   : {GROUP}")
print(f"⚙️  Режим   : {MODE}")
print("=" * 50)

# 🔹 Розміри деталей
sizes = {
    "XS": 80,
    "S":  90,
    "M":  100,
    "L":  110,
    "XL": 120
}

# 🔹 Довжина рулону:
#    - якщо запущено в Docker (немає TTY) або задано ENV → беремо з ENV або рандом
#    - якщо запущено локально з терміналом → запитуємо через input() як раніше
ROLL_LENGTH_ENV = os.environ.get("ROLL_LENGTH")

if ROLL_LENGTH_ENV:
    # задано явно через -e ROLL_LENGTH=...
    roll_length = int(ROLL_LENGTH_ENV)
    print(f"\n📏 Довжина рулону (з ENV): {roll_length} см")
elif not os.isatty(0):
    # Docker / неінтерактивний режим → рандомна довжина
    # Вибираємо значення, кратне НСК(80,90,100,110,120)=3960,
    # але щоб модель мала хоч якісь шаблони — беремо суми з допустимого набору
    candidates = []
    for r in range(1, 8):
        for combo in combinations_with_replacement(sizes.keys(), r):
            s = sum(sizes[k] for k in combo)
            if 200 <= s <= 800:
                candidates.append(s)
    candidates = sorted(set(candidates))
    roll_length = random.choice(candidates)
    print(f"\n📏 Довжина рулону (рандом, Docker): {roll_length} см")
else:
    # Локальний запуск — оригінальна поведінка
    print("\nВведіть довжину рулону (см):")
    roll_length = int(input("Довжина рулону: "))

# 🔹 Попит:
#    - якщо задано ENV → беремо з ENV
#    - якщо неінтерактивний режим → рандомний попит
#    - якщо локально → input() як раніше
DEMAND_ENV = os.environ.get("DEMAND_XS")  # перевіряємо лише одну як індикатор

if DEMAND_ENV is not None:
    demand = {
        "XS": int(os.environ.get("DEMAND_XS", "5")),
        "S":  int(os.environ.get("DEMAND_S",  "10")),
        "M":  int(os.environ.get("DEMAND_M",  "15")),
        "L":  int(os.environ.get("DEMAND_L",  "10")),
        "XL": int(os.environ.get("DEMAND_XL", "5")),
    }
    print(f"\n📦 Виробничий попит (з ENV): {demand}")
elif not os.isatty(0):
    demand = {size: random.randint(3, 20) for size in sizes}
    print(f"\n📦 Виробничий попит (рандом, Docker): {demand}")
else:
    print("\n📦 Введіть виробничий попит:")
    demand = {}
    for size in sizes:
        demand[size] = int(input(f"{size}: "))

# 🔹 Генерація шаблонів без залишків
max_parts = roll_length // min(sizes.values())
generated_templates = {}
template_id = 1

print("\n🔍 Генерація шаблонів без залишків:")
for r in range(1, max_parts + 1):
    for combo in combinations_with_replacement(sizes.keys(), r):
        total = sum(sizes[size] for size in combo)
        if total == roll_length:
            name = f"T{template_id}"
            generated_templates[name] = list(combo)
            print(f"{name}: {'+'.join(combo)}")
            template_id += 1

# 🔹 Перевірка на наявність шаблонів
if not generated_templates:
    print("\n⚠️ Немає жодного шаблону, який би точно заповнював рулон без залишку.")
    print("💡 Спробуйте змінити довжину рулону або дозволити шаблони з невеликим залишком.")
    exit()

# 🔹 Введення / автовибір недоступних шаблонів
EXCLUDED_ENV = os.environ.get("EXCLUDED_TEMPLATES")

if EXCLUDED_ENV is not None:
    excluded_input = EXCLUDED_ENV
    print(f"\n🚫 Недоступні шаблони (з ENV): {excluded_input or 'немає'}")
elif not os.isatty(0):
    excluded_input = ""
    print("\n🚫 Недоступні шаблони (Docker): не задано")
else:
    print("\n🚫 Вкажіть шаблони, які недоступні (наприклад: T2,T5), або залиште порожнім:")
    excluded_input = input("Недоступні шаблони: ").strip()

excluded_templates = set(excluded_input.split(",")) if excluded_input else set()
excluded_templates = {name.strip() for name in excluded_templates}

# 🔹 Фільтрація шаблонів
filtered_templates = {
    name: combo for name, combo in generated_templates.items()
    if name not in excluded_templates
}

# 🔹 Перевірка на наявність доступних шаблонів
if not filtered_templates:
    print("\n⚠️ Усі шаблони виключено. Оптимізація неможлива.")
    import sys
    sys.exit()

# 🔹 Створення моделі
model = LpProblem("Optimal_Cutting_Plan", LpMinimize)
variables = {}

# 🔹 Змінні для шаблонів
for name in filtered_templates:
    variables[name] = LpVariable(f"x_{name}", lowBound=0, cat=LpInteger)

# 🔹 Цільова функція
model += sum(variables[name] for name in filtered_templates), "Total_Rolls"

# 🔹 Обмеження на попит
for size in sizes:
    model += sum(variables[name] * filtered_templates[name].count(size)
                 for name in filtered_templates) >= demand[size], f"{size}_demand"

# 🔹 Розв'язання
model.solve()

# 🔹 Вивід результатів
print("\n📊 Оптимальний розподіл шаблонів:")
used_templates = {}
for name in filtered_templates:
    count = variables[name].varValue
    if count and count > 0:
        used_templates[name] = count
        print(f"{name} ({'+'.join(filtered_templates[name])}): {int(count)} рулонів")

total_rolls = int(value(model.objective))
print(f"✅ Загальна кількість рулонів: {total_rolls}")

# 🔹 Візуалізація (збережено оригінальну логіку + збереження у файл для Docker)
if used_templates:
    labels = [f"{name} ({'+'.join(filtered_templates[name])})" for name in used_templates]
    values_list = [used_templates[name] for name in used_templates]
    colors = plt.cm.tab20.colors

    plt.figure(figsize=(12, 6))
    bars = plt.bar(labels, values_list, color=colors[:len(labels)])
    plt.title(f'Оптимальний розподіл шаблонів розкрою\n'
              f'Студент: {STUDENT_NAME} | Група: {GROUP} | Режим: {MODE}')
    plt.ylabel('Кількість рулонів')
    plt.xlabel('Шаблони')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.5,
                 int(yval), ha='center', va='bottom')

    plt.tight_layout()

    # Зберігаємо діаграму у файл (працює і локально, і в Docker)
    output_path = os.environ.get("CHART_OUTPUT", "chart.png")
    plt.savefig(output_path, dpi=150)
    print(f"\n📈 Діаграму збережено: {output_path}")

    # Показуємо діаграму лише якщо є дисплей (локальний запуск)
    if os.isatty(0):
        plt.show()
else:
    print("\n⚠️ Немає даних для побудови діаграми.")
