# Build context: backend/
FROM python:3.12-slim
WORKDIR /app

COPY requirements-dev.txt ./requirements-dev.txt
COPY shared/ ./shared/
RUN pip install --no-cache-dir -r requirements-dev.txt && pip install --no-cache-dir ./shared

COPY services/catalog-service/ ./service/
WORKDIR /app/service
ENV PYTHONPATH=/app/service/src
EXPOSE 8000
CMD ["python", "-m", "catalog_service.run"]
