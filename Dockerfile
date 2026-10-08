# ==============================================================================
# SafeCart Production Dockerfile (Unified Frontend + Backend Container)
# ==============================================================================

# --- Stage 1: Build React Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/Frontend

COPY Frontend/package*.json ./
RUN npm install

COPY Frontend/ ./
RUN npm run build

# --- Stage 2: Python Backend Runtime ---
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY Backend/ ./Backend/
COPY Database/ ./Database/
COPY models/ ./models/
COPY utils/ ./utils/

# Copy built React artifacts into Frontend/dist
COPY --from=frontend-builder /app/Frontend/dist ./Frontend/dist

EXPOSE 8000

CMD ["sh", "-c", "uvicorn Backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
