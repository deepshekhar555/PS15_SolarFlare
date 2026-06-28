FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the ingestion module and fallback file
COPY data_ingest/ /app/data_ingest/
COPY telemetry_inline.json /app/telemetry_inline.json

EXPOSE 8001

# Run uvicorn
CMD ["uvicorn", "data_ingest.main:app", "--host", "0.0.0.0", "--port", "8001"]
