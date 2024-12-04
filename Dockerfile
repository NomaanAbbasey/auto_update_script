FROM python:3.10-slim

WORKDIR /app

# Copy files into the container
COPY update_gateway.py .
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the script
CMD ["python", "update_gateway.py"]