FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# .env is mounted at runtime — never baked into the image
ENV PORT=8103

EXPOSE 8103

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8103"]
