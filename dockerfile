# ---- Base image ----
    FROM python:3.11-slim

    # ---- Working directory ----
    WORKDIR /app
    
    # ---- Install dependencies ----
    RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates && \
        rm -rf /var/lib/apt/lists/*
    
    COPY requirements.txt ./
    COPY grobid_client_config.json ./
    RUN pip install --no-cache-dir -r requirements.txt
    
    # ---- Copy script ----
    COPY auto_import_ilibrarian.py ./
    
    # ---- Prepare folders ----
    RUN mkdir -p /app/new_papers /app/processed
    
    # ---- Read environment from docker-compose ----
    CMD ["python", "auto_import_ilibrarian.py"]
    