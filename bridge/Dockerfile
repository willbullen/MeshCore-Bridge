FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY meshcore_parser.py .
COPY meshcore_bridge.py .

# Run bridge
CMD ["python", "-u", "meshcore_bridge.py"]
