# Модель: Математичне моделювання оптимального розкрою рулонної тканини для виробництва футболок
# Автор: Жарук Данил, Холудієв Денис, група АІ-235

#!pip install pulp matplotlib

from pulp import LpProblem, LpVariable, LpMinimize, LpInteger, value
import matplotlib.pyplot as plt
from itertools import combinations_with_replacement

# 🔹 Розміри деталей
sizes = {
    "XS": 80,
    "S": 90,
    "M": 100,
    "L": 110,
    "XL": 120
}

# 🔹 Введення довжини рулону
print("Введіть довжину рулону (см):")
roll_length = int(input("Довжина рулону: "))

# 🔹 Генерація шаблонів без залишків
max_parts = roll_length // min(sizes.values())  # максимальна кількість деталей в одному рулоні
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


# 🔹 Введення недоступних шаблонів
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
    sys.exit()  # ⛔ Зупинка програми

# 🔹 Введення попиту
print("\n📦 Введіть виробничий попит:")
demand = {}
for size in sizes:
    demand[size] = int(input(f"{size}: "))

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
    model += sum(variables[name] * filtered_templates[name].count(size) for name in filtered_templates) >= demand[size], f"{size}_demand"

# 🔹 Розв’язання
model.solve()

# 🔹 Вивід результатів
print("\n📊 Оптимальний розподіл шаблонів:")
used_templates = {}
for name in filtered_templates:
    count = variables[name].varValue
    if count > 0:
        used_templates[name] = count
        print(f"{name} ({'+'.join(filtered_templates[name])}): {count} рулонів")
print(f"Загальна кількість рулонів: {value(model.objective)}")

# 🔹 Візуалізація
labels = [f"{name} ({'+'.join(filtered_templates[name])})" for name in used_templates]
values = [used_templates[name] for name in used_templates]
colors = plt.cm.tab20.colors  # набір кольорів

plt.figure(figsize=(12, 6))
bars = plt.bar(labels, values, color=colors[:len(labels)])
plt.title('Оптимальний розподіл шаблонів розкрою')
plt.ylabel('Кількість рулонів')
plt.xlabel('Шаблони')
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', linestyle='--', alpha=0.7)

for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 0.5, int(yval), ha='center', va='bottom')

plt.tight_layout()
plt.show()
