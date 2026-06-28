FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/storage/screenshots

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m app.seeds.run && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
