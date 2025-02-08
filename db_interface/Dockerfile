FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY DB_interface.py /app/
COPY monitoring.py /app/

EXPOSE 8003

CMD ["python", "DB_interface.py"]
