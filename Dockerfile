FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

# IMPORTANT: This is the “start command”.
# Do NOT set a Docker Command override in Render.
CMD ["bash", "-lc", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-10000} --log-level info"]
