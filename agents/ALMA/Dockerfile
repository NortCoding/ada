FROM python:3.11-slim
WORKDIR /app/ALMA
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
ENV AGENT_NAME=ALMA
EXPOSE 3011
CMD ["python", "src/agent_api.py"]
