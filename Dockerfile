FROM python:3.11-slim

# Debian'in ffmpeg paketi libass (altyazi render) destegiyle geliyor,
# Mac'te Homebrew'da yasadigimiz sorun burada olmuyor.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads outputs

ENV PORT=8080
EXPOSE 8080

# Tek worker sart: video sirasi (PROCESS_LOCK) ayni surecin icinde tutuluyor.
# Thread'ler, biri video yuklerken diger ziyaretcilerin sayfayi acabilmesini saglar.
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --worker-class gthread --threads 8 --timeout 600 app:app
