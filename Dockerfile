FROM python:3.12-slim

WORKDIR /app

# Install deps first for better layer cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code + optional dummy data
COPY server.py dummy_data.json .  # if dummy_data.json doesn't exist, it’s fine; Docker will warn, not fail, on Render

# Default port / command
ENV PORT=10000
CMD ["uvicorn","server:app","--host","0.0.0.0","--port","10000","--log-level","debug","--proxy-headers"]
