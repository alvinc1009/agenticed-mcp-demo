FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# If dummy_data.json exists, copy it; otherwise server falls back to in-code DB.
COPY server.py .
COPY dummy_data.json ./dummy_data.json

ENV PORT=10000
CMD ["uvicorn","server:app","--host","0.0.0.0","--port","10000","--log-level","debug","--proxy-headers"]
