FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY mqtt_data_preprocessor.py /app/
COPY monitoring.py /app/

EXPOSE 8002

CMD ["python", "mqtt_data_preprocessor.py"]
