FROM python:3.13-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . .

# Default command to run the backend
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
