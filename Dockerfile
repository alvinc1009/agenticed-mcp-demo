FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .

# Upgrade pip first, then install. Add -v for clearer errors if needed.
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# make sure these files exist at the repo root
COPY server.py dummy_data.json .

ENV PORT=10000
CMD ["uvicorn","server:app","--host","0.0.0.0","--port","10000","--log-level","debug","--proxy-headers"]
