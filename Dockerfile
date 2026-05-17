# ChatNet v2 — stack simples (TCP + proxy HTTP, sem build npm)
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV SERVER_HOST=127.0.0.1
ENV SERVER_PORT=9000
ENV HOST=0.0.0.0
ENV PORT=8080

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src/ /app/src/
COPY stack.py /app/stack.py

EXPOSE 8080
CMD ["python", "-m", "chatnet"]
