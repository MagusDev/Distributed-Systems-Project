FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY ml_model_trainer.py /app/

HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD ["python", "ml_model_trainer.py"]

CMD ["python", "ml_model_trainer.py"]
