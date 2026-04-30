# Модель: Математичне моделювання оптимального розкрою рулонної тканини для виробництва футболок
# Автор: Жарук Данил, група АІ-235

from flask import Flask, request, jsonify
from pulp import LpProblem, LpVariable, LpMinimize, LpInteger, value
from itertools import combinations_with_replacement

app = Flask(__name__)

SIZES = {
    "XS": 80,
    "S": 90,
    "M": 100,
    "L": 110,
    "XL": 120
}

def generate_templates(roll_length):
    max_parts = roll_length // min(SIZES.values())
    templates = {}
    template_id = 1
    for r in range(1, max_parts + 1):
        for combo in combinations_with_replacement(SIZES.keys(), r):
            total = sum(SIZES[size] for size in combo)
            if total == roll_length:
                templates[f"T{template_id}"] = list(combo)
                template_id += 1
    return templates

def solve_cutting(roll_length, demand, excluded_templates=None):
    if excluded_templates is None:
        excluded_templates = []

    all_templates = generate_templates(roll_length)

    if not all_templates:
        return None, "Немає жодного шаблону для цієї довжини рулону"

    filtered = {
        name: combo for name, combo in all_templates.items()
        if name not in excluded_templates
    }

    if not filtered:
        return None, "Усі шаблони виключено"

    model = LpProblem("Optimal_Cutting_Plan", LpMinimize)
    variables = {
        name: LpVariable(f"x_{name}", lowBound=0, cat=LpInteger)
        for name in filtered
    }

    model += sum(variables[name] for name in filtered), "Total_Rolls"

    for size in SIZES:
        model += (
            sum(variables[name] * filtered[name].count(size) for name in filtered)
            >= demand.get(size, 0)
        ), f"{size}_demand"

    model.solve()

    result = {}
    for name in filtered:
        count = variables[name].varValue
        if count and count > 0:
            result[name] = {
                "combo": "+".join(filtered[name]),
                "rolls": int(count)
            }

    return {
        "total_rolls": int(value(model.objective)),
        "plan": result,
        "all_templates": {
            name: "+".join(combo) for name, combo in all_templates.items()
        }
    }, None


@app.route('/calculate', methods=['GET', 'POST'])
def calculate():
    try:
        if request.method == 'POST':
            data = request.get_json(force=True) or {}
            roll_length = int(data.get('roll_length', 0))
            demand = data.get('demand', {})
            excluded = data.get('excluded_templates', [])
        else:
            roll_length = int(request.args.get('roll_length', 0))
            demand = {
                "XS": int(request.args.get('XS', 0)),
                "S":  int(request.args.get('S',  0)),
                "M":  int(request.args.get('M',  0)),
                "L":  int(request.args.get('L',  0)),
                "XL": int(request.args.get('XL', 0)),
            }
            excluded_raw = request.args.get('excluded_templates', '')
            excluded = [t.strip() for t in excluded_raw.split(',') if t.strip()]

        if roll_length <= 0:
            return jsonify({"error": "roll_length має бути більше 0"}), 400

        result, error = solve_cutting(roll_length, demand, excluded)
        if error:
            return jsonify({"error": error}), 400

        return jsonify({
            "input": {
                "roll_length": roll_length,
                "demand": demand,
                "excluded_templates": excluded
            },
            "result": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "info": "API оптимального розкрою тканини",
        "endpoint": "/calculate",
        "methods": ["GET", "POST"],
        "GET_example": "/calculate?roll_length=360&XS=2&S=3&M=5&L=2&XL=1",
        "POST_example": {
            "roll_length": 360,
            "demand": {"XS": 2, "S": 3, "M": 5, "L": 2, "XL": 1},
            "excluded_templates": []
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
