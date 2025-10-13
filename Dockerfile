FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

# Render will inject $PORT. Use it here.
CMD bash -lc 'uvicorn server:app --host 0.0.0.0 --port $PORT --log-level info'
