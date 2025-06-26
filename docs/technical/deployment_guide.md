# 部署指南

## 1. 部署概述

### 1.1 部署策略
本系统基于Label Studio构建，采用容器化部署方式，确保环境一致性和可扩展性。

### 1.2 部署架构
```
生产环境
├── 负载均衡器 (Nginx)
├── 应用服务器 (Django + Label Studio)
├── 数据库服务 (PostgreSQL)
├── 缓存服务 (Redis)
└── 文件存储 (本地/云存储)

开发环境
├── 本地开发服务器
├── SQLite/PostgreSQL
└── 本地Redis
```

## 2. 环境准备

### 2.1 系统要求

#### 最低配置
```
CPU: 4核
内存: 8GB
磁盘: 100GB SSD
操作系统: Ubuntu 20.04+ / CentOS 8+ / Docker
```

#### 推荐配置
```
CPU: 8核+
内存: 16GB+
磁盘: 500GB SSD
操作系统: Ubuntu 22.04 LTS
```

### 2.2 依赖软件安装

#### Docker方式 (推荐)
```bash
# 安装Docker和Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

#### 原生安装
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.9 python3-pip postgresql-14 redis-server nginx

# CentOS/RHEL
sudo yum update
sudo yum install python39 python3-pip postgresql14-server redis nginx
```

## 3. 项目部署

### 3.1 项目结构
```
label-studio-document-ocr/
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── requirements.txt
├── nginx.conf
├── .env.example
├── .env.prod.example
├── apps/
│   └── sensitive_entity_annotation/
├── static/
├── media/
├── data/
└── scripts/
    ├── setup.sh
    ├── deploy.sh
    └── backup.sh
```

### 3.2 配置文件

#### 3.2.1 Docker Compose (开发环境)
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DJANGO_SETTINGS_MODULE=label_studio.settings.local
      - LABEL_STUDIO_DB=postgresql://labelstudio:password@db:5432/labelstudio
      - REDIS_URL=redis://redis:6379/1
      - DEBUG=true
    volumes:
      - ./data:/label-studio/data
      - ./media:/label-studio/media
      - ./apps:/label-studio/apps
    depends_on:
      - db
      - redis
    command: ["python", "manage.py", "runserver", "0.0.0.0:8080"]

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: labelstudio
      POSTGRES_USER: labelstudio
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  celery:
    build: .
    environment:
      - DJANGO_SETTINGS_MODULE=label_studio.settings.local
      - LABEL_STUDIO_DB=postgresql://labelstudio:password@db:5432/labelstudio
      - REDIS_URL=redis://redis:6379/1
    volumes:
      - ./data:/label-studio/data
      - ./apps:/label-studio/apps
    depends_on:
      - db
      - redis
    command: ["celery", "-A", "label_studio.core", "worker", "-l", "info"]

volumes:
  postgres_data:
  redis_data:
```

#### 3.2.2 Docker Compose (生产环境)
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build: .
    environment:
      - DJANGO_SETTINGS_MODULE=label_studio.settings.production
      - LABEL_STUDIO_DB=postgresql://labelstudio:${DB_PASSWORD}@db:5432/labelstudio
      - REDIS_URL=redis://redis:6379/1
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
    volumes:
      - ./data:/label-studio/data
      - ./media:/label-studio/media
      - static_volume:/label-studio/static
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: labelstudio
      POSTGRES_USER: labelstudio
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - static_volume:/var/www/static
      - ./media:/var/www/media
    depends_on:
      - app
    restart: unless-stopped

  celery:
    build: .
    environment:
      - DJANGO_SETTINGS_MODULE=label_studio.settings.production
      - LABEL_STUDIO_DB=postgresql://labelstudio:${DB_PASSWORD}@db:5432/labelstudio
      - REDIS_URL=redis://redis:6379/1
    volumes:
      - ./data:/label-studio/data
    depends_on:
      - db
      - redis
    restart: unless-stopped
    command: ["celery", "-A", "label_studio.core", "worker", "-l", "info"]

  celery-beat:
    build: .
    environment:
      - DJANGO_SETTINGS_MODULE=label_studio.settings.production
      - LABEL_STUDIO_DB=postgresql://labelstudio:${DB_PASSWORD}@db:5432/labelstudio
      - REDIS_URL=redis://redis:6379/1
    volumes:
      - ./data:/label-studio/data
    depends_on:
      - db
      - redis
    restart: unless-stopped
    command: ["celery", "-A", "label_studio.core", "beat", "-l", "info"]

volumes:
  postgres_data:
  redis_data:
  static_volume:
```

#### 3.2.3 Dockerfile
```dockerfile
FROM heartexlabs/label-studio:1.10.1

# 设置工作目录
WORKDIR /label-studio

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目依赖
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 复制应用代码
COPY apps/ ./apps/
COPY static/ ./static/
COPY templates/ ./templates/
COPY settings/ ./settings/

# 复制启动脚本
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 设置环境变量
ENV LABEL_STUDIO_BASE_DATA_DIR=/label-studio/data
ENV LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
ENV LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=/label-studio/data
ENV PYTHONPATH=/label-studio

# 创建必要目录
RUN mkdir -p /label-studio/data /label-studio/media /label-studio/static

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health/ || exit 1

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
```

#### 3.2.4 Nginx配置
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                   '$status $body_bytes_sent "$http_referer" '
                   '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;
    
    # 基本设置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # 文件上传大小限制
    client_max_body_size 100M;
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # 上游服务器
    upstream labelstudio {
        server app:8080;
    }

    # 主站点配置
    server {
        listen 80;
        server_name _;
        
        # 重定向到HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name _;
        
        # SSL配置
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        
        # 静态文件
        location /static/ {
            alias /var/www/static/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
        
        location /media/ {
            alias /var/www/media/;
            expires 7d;
        }
        
        # 代理到应用服务器
        location / {
            proxy_pass http://labelstudio;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket支持
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # 健康检查
        location /health/ {
            proxy_pass http://labelstudio;
            access_log off;
        }
    }
}
```

### 3.3 启动脚本

#### 3.3.1 入口脚本
```bash
#!/bin/bash
# scripts/entrypoint.sh

set -e

# 等待数据库启动
echo "等待数据库启动..."
while ! pg_isready -h db -p 5432 -U labelstudio; do
    sleep 1
done

# 运行数据库迁移
echo "运行数据库迁移..."
python manage.py migrate --noinput

# 创建扩展表
echo "创建扩展表..."
python manage.py migrate sensitive_entity_annotation --noinput

# 收集静态文件
echo "收集静态文件..."
python manage.py collectstatic --noinput

# 创建超级用户（如果不存在）
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
    echo "创建超级用户..."
    python manage.py shell << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('超级用户创建成功')
else:
    print('超级用户已存在')
EOF
fi

# 初始化配置数据
echo "初始化配置数据..."
python manage.py shell << EOF
from apps.sensitive_entity_annotation.models import SystemConfig, EntityClassification
# 检查是否已初始化
if not SystemConfig.objects.filter(config_key='initialized').exists():
    # 初始化实体分类
    exec(open('scripts/init_entity_classification.py').read())
    # 标记已初始化
    SystemConfig.objects.create(config_key='initialized', config_value='true')
    print('配置数据初始化完成')
else:
    print('配置数据已存在')
EOF

echo "启动应用..."
exec "$@"
```

#### 3.3.2 部署脚本
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

# 配置变量
ENV_FILE=".env.prod"
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="./backups"
LOG_FILE="deploy.log"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 记录日志
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# 检查环境文件
if [ ! -f $ENV_FILE ]; then
    log "错误: 环境配置文件 $ENV_FILE 不存在"
    exit 1
fi

# 加载环境变量
source $ENV_FILE

log "开始部署敏感实体标注服务..."

# 1. 拉取最新代码
log "拉取最新代码..."
git pull origin main

# 2. 备份数据库
log "备份数据库..."
./scripts/backup.sh

# 3. 构建镜像
log "构建Docker镜像..."
docker-compose -f $COMPOSE_FILE build --no-cache

# 4. 停止旧服务
log "停止旧服务..."
docker-compose -f $COMPOSE_FILE down

# 5. 启动新服务
log "启动新服务..."
docker-compose -f $COMPOSE_FILE up -d

# 6. 等待服务启动
log "等待服务启动..."
sleep 30

# 7. 健康检查
log "执行健康检查..."
for i in {1..5}; do
    if curl -f http://localhost/health/ >/dev/null 2>&1; then
        log "健康检查通过"
        break
    else
        log "健康检查失败，重试中..."
        sleep 10
    fi
    
    if [ $i -eq 5 ]; then
        log "健康检查失败，部署可能有问题"
        exit 1
    fi
done

# 8. 显示服务状态
log "显示服务状态..."
docker-compose -f $COMPOSE_FILE ps

log "部署完成！"
log "访问地址: https://$(hostname)"
```

#### 3.3.3 备份脚本
```bash
#!/bin/bash
# scripts/backup.sh

set -e

# 配置
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_CONTAINER="label-studio-document-ocr_db_1"
REDIS_CONTAINER="label-studio-document-ocr_redis_1"

# 创建备份目录
mkdir -p $BACKUP_DIR

echo "开始备份..."

# 1. 备份数据库
echo "备份PostgreSQL数据库..."
docker exec $DB_CONTAINER pg_dump -U labelstudio labelstudio | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# 2. 备份Redis
echo "备份Redis数据..."
docker exec $REDIS_CONTAINER redis-cli --rdb /tmp/dump.rdb
docker cp $REDIS_CONTAINER:/tmp/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"

# 3. 备份文件数据
echo "备份文件数据..."
tar -czf "$BACKUP_DIR/data_$DATE.tar.gz" data/ media/

# 4. 清理旧备份
echo "清理7天前的备份..."
find $BACKUP_DIR -name "*.gz" -o -name "*.rdb" | head -n -21 | xargs rm -f

echo "备份完成，文件保存在: $BACKUP_DIR"
ls -la $BACKUP_DIR/*$DATE*
```

## 4. 环境配置

### 4.1 环境变量

#### 开发环境 (.env)
```bash
# 基础配置
DEBUG=true
SECRET_KEY=your-secret-key-for-development
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库配置
DB_PASSWORD=password

# Redis配置
REDIS_PASSWORD=

# 超级用户
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin123

# 敏感实体标注配置
MAX_BATCH_IMPORT_SIZE=1000
ENABLE_AUTO_VALIDATION=true
QUALITY_THRESHOLD=0.95
```

#### 生产环境 (.env.prod)
```bash
# 基础配置
DEBUG=false
SECRET_KEY=your-very-secure-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# 数据库配置
DB_PASSWORD=your-secure-db-password

# Redis配置
REDIS_PASSWORD=your-secure-redis-password

# 超级用户
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@yourdomain.com
DJANGO_SUPERUSER_PASSWORD=your-secure-admin-password

# 邮件配置
EMAIL_HOST=smtp.yourdomain.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your-email-password

# 敏感实体标注配置
MAX_BATCH_IMPORT_SIZE=2000
ENABLE_AUTO_VALIDATION=true
QUALITY_THRESHOLD=0.95
ANNOTATION_TIMEOUT_MINUTES=30

# 监控配置
SENTRY_DSN=your-sentry-dsn
```

### 4.2 SSL证书配置

#### 自签名证书 (开发)
```bash
# 生成自签名证书
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem \
    -out ssl/cert.pem \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=Development/CN=localhost"
```

#### Let's Encrypt证书 (生产)
```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot certonly --standalone -d yourdomain.com

# 复制证书到项目目录
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*
```

## 5. 快速部署

### 5.1 一键部署脚本
```bash
#!/bin/bash
# scripts/quick_deploy.sh

set -e

echo "敏感实体标注服务一键部署脚本"
echo "================================"

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "Docker未安装，正在安装..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose未安装，正在安装..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 克隆项目
if [ ! -d "label-studio-document-ocr" ]; then
    echo "克隆项目代码..."
    git clone https://github.com/your-org/label-studio-document-ocr.git
    cd label-studio-document-ocr
else
    cd label-studio-document-ocr
    git pull origin main
fi

# 复制环境配置
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "请编辑 .env 文件配置环境变量"
    echo "按任意键继续..."
    read -n 1
fi

# 生成SSL证书
if [ ! -f "ssl/cert.pem" ]; then
    echo "生成自签名SSL证书..."
    mkdir -p ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -subj "/C=CN/ST=Beijing/L=Beijing/O=Development/CN=localhost"
fi

# 启动服务
echo "启动服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 30

# 健康检查
if curl -f http://localhost:8080/health/ >/dev/null 2>&1; then
    echo "部署成功！"
    echo "访问地址: http://localhost:8080"
    echo "管理员账号: admin / admin123"
else
    echo "部署可能有问题，请检查日志"
    docker-compose logs
fi
```

### 5.2 使用方式
```bash
# 下载并运行一键部署脚本
curl -fsSL https://raw.githubusercontent.com/your-org/label-studio-document-ocr/main/scripts/quick_deploy.sh -o quick_deploy.sh
chmod +x quick_deploy.sh
./quick_deploy.sh
```

## 6. 监控和维护

### 6.1 日志管理
```bash
# 查看应用日志
docker-compose logs -f app

# 查看数据库日志
docker-compose logs -f db

# 查看Nginx日志
docker-compose logs -f nginx

# 查看所有服务状态
docker-compose ps
```

### 6.2 性能监控
```bash
# 系统资源监控
docker stats

# 数据库性能监控
docker exec -it db psql -U labelstudio -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# Redis监控
docker exec -it redis redis-cli info memory
```

### 6.3 定期维护
```bash
# 每日备份任务
cat > /etc/cron.d/labelstudio-backup << EOF
0 2 * * * root /path/to/label-studio-document-ocr/scripts/backup.sh
EOF

# 每周清理日志
cat > /etc/cron.d/labelstudio-cleanup << EOF
0 3 * * 0 root docker system prune -f
EOF
```

## 7. 故障排除

### 7.1 常见问题

#### 数据库连接失败
```bash
# 检查数据库状态
docker-compose logs db

# 测试数据库连接
docker exec -it app pg_isready -h db -p 5432
```

#### 静态文件不显示
```bash
# 重新收集静态文件
docker exec -it app python manage.py collectstatic --noinput

# 检查Nginx配置
docker exec -it nginx nginx -t
```

#### 内存不足
```bash
# 调整Docker内存限制
echo "memory.limit_in_bytes = 2G" >> docker-compose.yml

# 监控内存使用
docker stats --no-stream
```

### 7.2 调试命令
```bash
# 进入应用容器
docker exec -it app bash

# 运行Django shell
docker exec -it app python manage.py shell

# 检查数据库迁移状态
docker exec -it app python manage.py showmigrations

# 重启服务
docker-compose restart app
```

这个部署指南提供了完整的部署方案，从开发环境到生产环境的全流程覆盖，确保系统能够快速、稳定地部署和运行。