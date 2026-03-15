FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-kor \
    fonts-nanum \
    && rm -rf /var/lib/apt/lists/*

# 변경점 1: 폴더를 만든 후, 누구나 접근할 수 있도록 777 권한 부여
RUN mkdir -p /tmp/chrome-data /tmp/chrome-crashes && \
    chmod -R 777 /tmp/chrome-data /tmp/chrome-crashes

# 변경점 2: 일반 사용자 권한으로 실행될 때를 대비해 가상의 HOME 환경변수를 /tmp로 지정
ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    RUNNING_IN_DOCKER=true \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
