# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Копируем requirements.txt
COPY requirements.txt .

# Устанавливаем без компиляции
RUN pip install --only-binary=all --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

EXPOSE 8000
CMD ["python", "-m", "web.main"]