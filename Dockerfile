FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED 1
ENV PORT=10000

EXPOSE ${PORT}

CMD gunicorn --bind 0.0.0.0:${PORT} app:app