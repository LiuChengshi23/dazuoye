FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt update && apt install -y \
    iputils-ping \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝源码
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]