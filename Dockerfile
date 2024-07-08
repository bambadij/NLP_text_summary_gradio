FROM python:3.9

WORKDIR /app 
 
COPY . /app/
RUN pip install --upgrade pip
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    libtesseract-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt 

RUN mkdir -p /app/.cache && chmod -R 777 /app/.cache
ENV TRANSFORMERS_CACHE=/app/.cache
ENV HF_HOME=/app/.cache 
 
#EXPOSE 7860 
CMD ["python", "app.py","--host", "0.0.0.0", "--port", "7860"]
