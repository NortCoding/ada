FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/
ENV PYTHONPATH=/app
EXPOSE 3007

CMD ["uvicorn", "simulation_api:app", "--host", "0.0.0.0", "--port", "3007"]
