FROM python:3.9-slim

WORKDIR /app

# 安装必要的系统工具
RUN apt-get update && apt-get install -y \
    openssh-client \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
