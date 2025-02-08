FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY anomaly_detect.py /app/
COPY monitoring.py /app/

EXPOSE 8006

CMD ["python", "anomaly_detect.py"]
