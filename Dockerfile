# Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Запускаем через Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "web.main:app"]