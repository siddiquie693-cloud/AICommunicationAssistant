FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY ai /app/ai

WORKDIR /app/backend

EXPOSE 8000

CMD ["python", "-m", "daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
