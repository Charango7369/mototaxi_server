FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/app/static/fotos

COPY start.sh /start.sh
RUN chmod +x /start.sh

ENTRYPOINT ["sh", "-c", "/start.sh"]
