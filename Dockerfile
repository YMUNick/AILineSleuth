# LineSleuth: single Cloud Run service (FastAPI API + static front end)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
# Bake the deterministic dataset into the image (used by QUERY_BACKEND=local; harmless with bigquery)
RUN python -m app.data.generate

RUN useradd --create-home appuser
USER appuser

# One worker: investigation state lives in process memory (see docs/engineering/architecture.md)
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --proxy-headers --forwarded-allow-ips="*"
