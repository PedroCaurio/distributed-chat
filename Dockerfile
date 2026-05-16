# Build front-end (servido pelo cliente HTTP)
FROM node:20-slim AS frontend-build
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stack: servidor TCP + cliente HTTP
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV CHAT_SERVER_HOST=127.0.0.1
ENV CHAT_SERVER_PORT=9000
ENV CHAT_HOST=0.0.0.0
ENV PORT=8080

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY common /app/common
COPY server /app/server
COPY client /app/client
COPY stack /app/stack
COPY --from=frontend-build /fe/dist /app/frontend/dist

EXPOSE 8080
CMD ["python", "-m", "stack"]
