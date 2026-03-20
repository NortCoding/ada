FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema operativo (git, curl) y Node.js para el CODE agent
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/
ENV PYTHONPATH=/app
EXPOSE 3003

CMD ["uvicorn", "task_runner_api:app", "--host", "0.0.0.0", "--port", "3003"]
