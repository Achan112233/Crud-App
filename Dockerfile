FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for ODBC (needed for Azure SQL)
RUN apt-get update && apt-get install -y \
    gcc \
    unixodbc-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run app
CMD ["python", "app.py"]
