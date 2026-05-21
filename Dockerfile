# Модель: Математичне моделювання оптимального розкрою рулонної тканини
# Автор: Жарук Данил, Холудієв Денис, група АІ-235

FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "api.py"]
