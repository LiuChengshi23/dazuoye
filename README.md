## 📋 项目概述

本项目是一个**企业级服务器实时监控数据大屏系统**，采用前后端分离架构，实现了完全自动化的服务器监控管理。系统通过Web界面统一管理多台服务器，自动采集CPU、内存、磁盘等关键指标，并通过可视化大屏实时展示。

### 🎯 核心功能

1. **Web主机管理界面**：添加/删除被监控主机
2. **自动化数据采集**：通过SSH自动采集服务器性能指标
3. **实时监控大屏**：可视化展示所有服务器运行状态
4. **历史数据查询**：按时间范围查询历史监控数据
5. **智能告警系统**：可配置阈值，自动告警提示
6. **容器化部署**：基于Docker的轻量级部署方案

### 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                        前端展示层                            │
├─────────────────────────────────────────────────────────┤
│  index.html     dashboard.html     history.html     settings.html │
│  (主机管理)      (监控大屏)        (历史记录)        (系统设置)     │
├─────────────────────────────────────────────────────────┤
│                        Nginx反向代理                          │
├─────────────────────────────────────────────────────────┤
│                      API接口层                              │
│                    (Flask REST API)                         │
├─────────────────────────────────────────────────────────┤
│                      业务逻辑层                              │
│                 (数据处理 + SSH采集)                        │
├─────────────────────────────────────────────────────────┤
│                      数据存储层                              │
│                     (SQLite数据库)                            │
├─────────────────────────────────────────────────────────┤
│                    被监控服务器集群                            │
│              (SSH连接 + 性能指标采集)                       │
└─────────────────────────────────────────────────────────┘
```

### 🛠️ 技术栈

- **后端**：Python 3.8 + Flask + SQLite
- **前端**：HTML5 + CSS3 + JavaScript + Chart.js
- **容器化**：Docker + Docker Compose
- **数据采集**：Paramiko (SSH)
- **可视化**：Chart.js图表库

------

## 📁 项目结构

```
project
├── docker-compose.yml              # Docker编排配置
├── README.md                       # 项目说明文档
├── 
├── backend/                        # 后端服务目录
│   ├── app.py                      # Flask主应用文件
│   ├── Dockerfile                   # 后端Docker镜像构建文件
│   ├── requirements.txt             # Python依赖包列表
│   └── data/                        # 数据存储目录
│       └── monitor.db               # SQLite数据库文件
│
└── frontend/                      # 前端服务目录
    ├── index.html                  # 主机管理页面
    ├── dashboard.html              # 监控大屏页面
    ├── history.html                # 历史记录页面
    ├── settings.html               # 系统设置页面
    ├── 
    ├── css/                        # 样式文件目录
    │   └── style.css               # 主样式文件
    │
    ├── js/                         # JavaScript文件目录
    │   ├── ui.js                   # UI工具库
    │   ├── api.js                  # API接口封装
    │   └── charts.js              # 图表管理模块
    │   └── i18n/                      
    │    └── en.js
    │    └── index.js
    │    └── zh.js
```

------

## 🚀 部署步骤

### 第一步：环境准备

#### 1.1 系统要求

- **操作系统**：Linux (Ubuntu 20.04+ / CentOS 8+) 或 macOS
- **内存**：最低2GB，推荐4GB+
- **存储**：最低10GB可用空间
- **网络**：能够访问互联网（用于下载依赖）

#### 1.2 软件依赖安装

**Ubuntu/Debian系统：**

bash

```
# 更新包管理器
sudo apt update

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 将当前用户添加到docker组
sudo usermod -aG docker $USER
newgrp docker
```

**CentOS/RHEL系统：**

bash

```
# 安装Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker
```

#### 1.3 验证安装

bash

```
# 验证Docker版本
docker --version

# 验证Docker Compose版本
docker-compose --version

# 测试Docker运行
docker run hello-world
```

### 第二步：获取项目代码

#### 2.1 克隆项目仓库

bash

```
# 克隆项目到本地
git clone <项目仓库地址>
cd monitor-system

# 查看项目结构
ls -la
```

#### 2.2 项目文件说明

bash

```
# 查看Docker编排配置
cat docker-compose.yml

# 查看后端依赖
cat backend/requirements.txt

# 查看前端页面结构
ls -la frontend/
```

### 第三步：配置系统参数

#### 3.1 docker-compose.yml配置

yaml

```
version: "3.8"

services:
  backend:
    build: ./backend
    container_name: monitor-backend
    network_mode: "host"  # 使用宿主机网络
    restart: unless-stopped
    volumes:
      - ./backend:/app
      - ./backend/data:/app/data
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=True

  frontend:
    image: nginx:alpine
    container_name: monitor-frontend
    volumes:
      - ./frontend:/usr/share/nginx/html
    ports:
      - "8080:80"  # 前端访问端口
    restart: unless-stopped
    depends_on:
      - backend
```

#### 3.2 后端配置文件

bash

```
# 后端Dockerfile
FROM python:3.8-slim

WORKDIR /app

# 配置国内镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 更新pip
RUN pip install --upgrade pip setuptools wheel

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "app.py"]
```

#### 3.3 requirements.txt

txt

```
flask==2.0.3
paramiko==2.8.0
```

### 第四步：构建和启动系统

#### 4.1 构建Docker镜像

bash

```
# 在项目根目录执行
cd monitor-system

# 构建所有服务镜像
docker-compose build

# 查看构建的镜像
docker images | grep monitor
```

#### 4.2 启动系统服务

bash

```
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f
```

#### 4.3 验证系统启动

bash

```
# 检查后端API
curl http://localhost:5000/api/hosts

# 检查前端页面
curl -I http://localhost:8080

# 查看容器资源使用
docker stats
```

### 第五步：访问和验证系统

#### 5.1 访问Web界面

打开浏览器访问以下地址：

- **主机管理**：http://localhost:8080/index.html
- **监控大屏**：http://localhost:8080/dashboard.html
- **历史记录**：http://localhost:8080/history.html
- **系统设置**：http://localhost:8080/settings.html

#### 5.2 系统初始化验证

1. **检查页面加载**：确保所有页面正常显示
2. **验证API接口**：测试主机管理、数据查询等接口

3. **检查数据库**：确认SQLite数据库正常创建
