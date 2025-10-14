FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Include dummy data if you want the profile tool
COPY server.py dummy_data.json .  # if you don’t have dummy_data.json yet, change to: COPY server.py .

ENV PORT=10000
CMD ["uvicorn","server:app","--host","0.0.0.0","--port","10000","--proxy-headers","--log-level","debug"]
