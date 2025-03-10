FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt uvicorn

COPY API_gateway.py /app/
COPY monitoring.py /app/

EXPOSE 8000
EXPOSE 8004

# Update CMD to use uvicorn with proper host binding
CMD ["uvicorn", "API_gateway:app", "--host", "0.0.0.0", "--port", "8000"]
