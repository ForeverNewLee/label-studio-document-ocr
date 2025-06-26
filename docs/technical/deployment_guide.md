# 部署指南 (极简版)

## 1. 部署概述

### 1.1 部署策略
基于Label Studio单体部署，追求最简单、最可靠的部署方式。

### 1.2 架构选择
```
极简架构
├── Label Studio (单一服务)
├── SQLite/PostgreSQL (单一数据库)
└── 本地文件存储
```

## 2. 环境准备

### 2.1 系统要求

#### 最低配置
```
CPU: 2核
内存: 4GB
磁盘: 50GB
操作系统: Ubuntu 20.04+ / Windows 10+ / macOS 10.15+
Python: 3.8+
```

#### 推荐配置
```
CPU: 4核
内存: 8GB
磁盘: 100GB SSD
操作系统: Ubuntu 22.04 LTS
Python: 3.9+
```

### 2.2 Python环境准备

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip

# macOS (使用Homebrew)
brew install python3

# Windows
# 从 python.org 下载安装Python 3.9+
```

## 3. 快速部署 (5分钟)

### 3.1 一键部署脚本

```bash
#!/bin/bash
# setup.sh - 一键部署脚本

echo "🚀 开始部署Label Studio敏感实体标注服务..."

# 1. 创建项目目录
mkdir -p label-studio-document-ocr
cd label-studio-document-ocr

# 2. 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装Label Studio
pip install --upgrade pip
pip install label-studio

# 4. 创建必要目录
mkdir -p {demo_data,scripts,configs,exports}

# 5. 启动Label Studio
echo "✅ 安装完成！启动服务..."
label-studio start --host 0.0.0.0 --port 8080

echo "🎉 部署完成！"
echo "📝 访问地址: http://localhost:8080"
echo "👤 首次访问将创建管理员账户"
```

### 3.2 手动部署步骤

```bash
# 步骤1: 创建项目目录
mkdir label-studio-document-ocr
cd label-studio-document-ocr

# 步骤2: 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 步骤3: 安装Label Studio
pip install label-studio

# 步骤4: 启动服务
label-studio start

# 步骤5: 访问系统
# 浏览器打开 http://localhost:8080
```

## 4. 项目配置

### 4.1 创建项目结构

```bash
# 创建完整目录结构
mkdir -p {demo_data,scripts,configs,exports,backups}

# 创建必要文件
touch requirements.txt
touch configs/entity_labeling_config.xml
touch scripts/import_tasks.py
touch scripts/export_results.py
```

### 4.2 配置文件

#### requirements.txt
```
label-studio>=1.10.0
requests>=2.28.0
```

#### configs/entity_labeling_config.xml
```xml
<View>
  <Header value="敏感实体标注任务"/>
  <Text value="识别文档中的所有敏感实体(包括被[MASK]遮挡的)并进行分类标注"/>
  
  <Text name="text" value="$ocr_content" style="white-space: pre-wrap"/>
  
  <Labels name="entity_type" toName="text">
    <!-- 人名相关 -->
    <Label value="FullName" background="red" hotkey="1"/>
    <Label value="FirstName" background="darkred" hotkey="2"/>  
    <Label value="LastName" background="lightcoral" hotkey="3"/>
    
    <!-- 地址相关 -->
    <Label value="Address" background="blue" hotkey="4"/>
    <Label value="StreetNumber" background="darkblue" hotkey="5"/>
    <Label value="StreetName" background="lightblue" hotkey="6"/>
    <Label value="City" background="navy" hotkey="7"/>
    <Label value="State" background="skyblue" hotkey="8"/>
    <Label value="ZipCode" background="steelblue" hotkey="9"/>
    
    <!-- 证件号码 -->
    <Label value="InvoiceNumber" background="green" hotkey="q"/>
    <Label value="CompanyName" background="darkgreen" hotkey="w"/>
    <Label value="CheckNumber" background="lightgreen" hotkey="e"/>
    
    <!-- 时间信息 -->
    <Label value="Date" background="orange" hotkey="r"/>
    <Label value="MilitaryAddress" background="purple" hotkey="t"/>
  </Labels>
</View>
```

## 5. 数据导入导出

### 5.1 批量导入脚本

```python
# scripts/import_tasks.py
#!/usr/bin/env python3
import json
import requests
from pathlib import Path
import argparse

def import_tasks(api_url, api_token, project_id, data_dir):
    """批量导入OCR文档到Label Studio"""
    
    tasks = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"❌ 数据目录不存在: {data_dir}")
        return
    
    # 读取所有txt文件
    for txt_file in data_path.glob("*.txt"):
        print(f"📄 处理文件: {txt_file.name}")
        
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        task = {
            "data": {
                "ocr_content": content,
                "document_name": txt_file.name
            }
        }
        tasks.append(task)
    
    if not tasks:
        print("❌ 未找到任何txt文件")
        return
    
    # 调用Label Studio API
    print(f"📤 导入 {len(tasks)} 个任务到项目 {project_id}")
    
    response = requests.post(
        f"{api_url}/api/projects/{project_id}/import",
        headers={"Authorization": f"Token {api_token}"},
        json=tasks
    )
    
    if response.status_code == 201:
        print(f"✅ 成功导入 {len(tasks)} 个任务")
    else:
        print(f"❌ 导入失败: {response.status_code} - {response.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='批量导入OCR文档')
    parser.add_argument('--api-url', default='http://localhost:8080', help='Label Studio API地址')
    parser.add_argument('--api-token', required=True, help='API Token')
    parser.add_argument('--project-id', required=True, type=int, help='项目ID')
    parser.add_argument('--data-dir', default='./demo_data', help='数据目录')
    
    args = parser.parse_args()
    import_tasks(args.api_url, args.api_token, args.project_id, args.data_dir)
```

### 5.2 结果导出脚本

```python
# scripts/export_results.py
#!/usr/bin/env python3
import json
import requests
import csv
import argparse
from datetime import datetime

def export_annotations(api_url, api_token, project_id, output_file):
    """导出标注结果"""
    
    print(f"📥 从项目 {project_id} 导出标注结果...")
    
    # 获取标注结果
    response = requests.get(
        f"{api_url}/api/projects/{project_id}/export",
        headers={"Authorization": f"Token {api_token}"},
        params={"exportType": "JSON"}
    )
    
    if response.status_code != 200:
        print(f"❌ 导出失败: {response.status_code} - {response.text}")
        return
    
    annotations = response.json()
    
    # 生成CSV文件
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Document', 'Entity_Text', 'Entity_Label', 'Start_Pos', 'End_Pos', 'Annotator'])
        
        exported_count = 0
        for annotation in annotations:
            document = annotation['data'].get('document_name', 'unknown')
            
            for ann_result in annotation.get('annotations', []):
                annotator = ann_result.get('completed_by', 'unknown')
                
                for entity in ann_result.get('result', []):
                    if entity.get('type') == 'labels':
                        writer.writerow([
                            document,
                            entity['value']['text'],
                            entity['value']['labels'][0],
                            entity['value']['start'],
                            entity['value']['end'],
                            annotator
                        ])
                        exported_count += 1
    
    print(f"✅ 导出完成: {exported_count} 个实体标注 -> {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='导出标注结果')
    parser.add_argument('--api-url', default='http://localhost:8080', help='Label Studio API地址')
    parser.add_argument('--api-token', required=True, help='API Token')
    parser.add_argument('--project-id', required=True, type=int, help='项目ID')
    parser.add_argument('--output', default=f'./exports/annotations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv', help='输出文件')
    
    args = parser.parse_args()
    export_annotations(args.api_url, args.api_token, args.project_id, args.output)
```

## 6. 生产环境部署

### 6.1 PostgreSQL配置 (可选)

```bash
# 安装PostgreSQL
sudo apt install postgresql postgresql-contrib

# 创建数据库
sudo -u postgres createuser labelstudio
sudo -u postgres createdb labelstudio_db -O labelstudio
sudo -u postgres psql -c "ALTER USER labelstudio PASSWORD 'your_password';"

# 配置Label Studio使用PostgreSQL
export LABEL_STUDIO_DB=postgresql://labelstudio:your_password@localhost:5432/labelstudio_db
```

### 6.2 Docker部署 (可选)

```yaml
# docker-compose.yml
version: '3.8'

services:
  labelstudio:
    image: heartexlabs/label-studio:latest
    ports:
      - "8080:8080"
    environment:
      - LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
      - LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=/label-studio/data
      - LABEL_STUDIO_DB=${LABEL_STUDIO_DB:-}
    volumes:
      - ./data:/label-studio/data
      - ./media:/label-studio/media
      - labelstudio_db:/label-studio/db
    restart: unless-stopped

volumes:
  labelstudio_db:
```

```bash
# 启动Docker服务
docker-compose up -d

# 查看服务状态
docker-compose logs -f labelstudio
```

### 6.3 系统服务配置

```ini
# /etc/systemd/system/labelstudio.service
[Unit]
Description=Label Studio Service
After=network.target

[Service]
Type=simple
User=labelstudio
WorkingDirectory=/opt/label-studio-document-ocr
Environment=PATH=/opt/label-studio-document-ocr/venv/bin
ExecStart=/opt/label-studio-document-ocr/venv/bin/label-studio start --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启用系统服务
sudo systemctl enable labelstudio
sudo systemctl start labelstudio
sudo systemctl status labelstudio
```

## 7. 运维管理

### 7.1 日常维护

```bash
# 数据备份
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
if [ -f "~/.local/share/label-studio/label_studio.sqlite3" ]; then
    cp ~/.local/share/label-studio/label_studio.sqlite3 $BACKUP_DIR/db_$DATE.sqlite3
    echo "✅ 数据库备份完成: $BACKUP_DIR/db_$DATE.sqlite3"
fi

# 备份媒体文件
if [ -d "~/.local/share/label-studio/media" ]; then
    tar -czf $BACKUP_DIR/media_$DATE.tar.gz ~/.local/share/label-studio/media
    echo "✅ 媒体文件备份完成: $BACKUP_DIR/media_$DATE.tar.gz"
fi

echo "🎉 备份完成！"
```

### 7.2 监控检查

```bash
# scripts/health_check.sh
#!/bin/bash

API_URL="http://localhost:8080"

# 检查服务状态
if curl -f $API_URL/health/ > /dev/null 2>&1; then
    echo "✅ Label Studio服务正常"
else
    echo "❌ Label Studio服务异常"
    exit 1
fi

# 检查磁盘空间
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "⚠️  磁盘空间不足: ${DISK_USAGE}%"
fi

echo "📊 系统状态检查完成"
```

## 8. 故障排除

### 8.1 常见问题

#### 问题1: 端口被占用
```bash
# 查找占用8080端口的进程
sudo lsof -i :8080

# 杀死进程
sudo kill -9 <PID>

# 或使用其他端口
label-studio start --port 8081
```

#### 问题2: 权限问题
```bash
# 确保目录权限正确
chmod -R 755 ~/.local/share/label-studio/
chown -R $USER:$USER ~/.local/share/label-studio/
```

#### 问题3: 内存不足
```bash
# 检查内存使用
free -h

# 清理系统缓存
sudo sync && sudo sysctl vm.drop_caches=3
```

### 8.2 日志分析

```bash
# 查看Label Studio日志
tail -f ~/.local/share/label-studio/logs/label_studio.log

# 或者如果使用Docker
docker-compose logs -f labelstudio
```

## 9. 快速开始总结

### 9.1 最快部署 (3分钟)

```bash
# 一行命令安装并启动
pip install label-studio && label-studio start
```

### 9.2 完整部署 (10分钟)

```bash
# 1. 克隆项目
git clone <repository>
cd label-studio-document-ocr

# 2. 运行部署脚本
bash setup.sh

# 3. 访问系统
open http://localhost:8080
```

### 9.3 系统特色

- **极简部署**: 最少依赖，最快上线
- **零配置**: 开箱即用，无需复杂设置  
- **易扩展**: 需要时可快速升级到复杂架构
- **易维护**: 单一服务，故障排除简单

---

**部署成功标志**: 访问 http://localhost:8080 能看到Label Studio登录界面