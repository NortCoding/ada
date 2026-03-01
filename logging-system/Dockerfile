FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
WORKDIR /app/src
ENV PYTHONPATH=/app/src

ENV LOGGING_PORT=3006
EXPOSE 3006

CMD ["uvicorn", "logging_api:app", "--host", "0.0.0.0", "--port", "3006"]
