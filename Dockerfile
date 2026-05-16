# Build front-end
FROM node:20-slim AS frontend-build
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# API + static
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV ENABLE_TCP_SERVER=false
ENV PORT=8080

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY common /app/common
COPY server /app/server
COPY --from=frontend-build /fe/dist /app/frontend/dist

EXPOSE 8080
CMD ["python", "-m", "server"]
