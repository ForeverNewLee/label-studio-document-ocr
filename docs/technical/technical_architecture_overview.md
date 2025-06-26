# 敏感实体标注服务技术架构总览 (简化版)

## 1. 架构设计原则

### 1.1 核心原则
- **基于Label Studio**: 充分利用Label Studio现有能力，最小化定制开发
- **最简架构**: 仅使用必要的组件，避免过度工程化
- **快速部署**: 一键启动，5分钟内可用
- **数据安全**: 保障敏感数据安全，支持数据脱敏需求

### 1.2 技术约束
- 必须基于现有Label Studio平台
- 保持与Label Studio生态兼容
- 优先使用Label Studio内置功能
- 最小化外部依赖

## 2. 简化架构设计

### 2.1 系统架构图
```
┌─────────────────────────────────────────────────────────────┐
│                Label Studio + 自定义标注模板                  │
├─────────────────────────────────────────────────────────────┤
│  敏感实体标注界面  │  批量导入脚本  │  结果导出功能           │
└─────────────────────┬───────────────────────────────────────┘
                     │
┌─────────────────────┴───────────────────────────────────────┐
│           数据存储 (SQLite/PostgreSQL)                     │
│           + 本地文件存储                                    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件 (极简版)

#### 2.2.1 Label Studio Core
- **版本**: Label Studio Community Edition (最新stable版本)
- **作用**: 提供全部功能 - 标注界面、用户管理、项目管理
- **定制**: 仅通过配置和标注模板定制，零代码修改

#### 2.2.2 必要扩展 (最小化)
- **敏感实体标注模板**: 专门的NER标注配置
- **批量导入脚本**: Python脚本实现批量任务导入
- **结果导出脚本**: Python脚本实现标注结果导出

## 3. 极简技术选型

### 3.1 基础技术栈

| 组件 | 选型 | 说明 |
|-----|------|------|
| 标注平台 | Label Studio | 开源数据标注平台 |
| 数据库 | SQLite (开发) / PostgreSQL (生产) | Label Studio内置支持 |
| 存储 | 本地文件系统 | 无需对象存储 |
| 部署 | Python虚拟环境 / Docker (可选) | 简单部署 |

### 3.2 移除的组件 (简化)
- ❌ Redis缓存 - 使用Label Studio默认配置
- ❌ Celery任务队列 - 直接处理，无需异步
- ❌ Nginx负载均衡 - 开发阶段无需
- ❌ 复杂的扩展表 - 仅使用Label Studio原生表
- ❌ 质量控制模块 - 使用Label Studio内置审核功能
- ❌ 统计分析模块 - 通过Label Studio界面查看

## 4. 标注模板配置 (核心)

### 4.1 敏感实体标注模板
```xml
<View>
  <!-- 任务指令 -->
  <Header value="敏感实体标注任务"/>
  <Text value="识别文档中的所有敏感实体(包括被[MASK]遮挡的)并进行分类标注"/>
  
  <!-- 文档内容 -->
  <Text name="text" value="$ocr_content" style="white-space: pre-wrap"/>
  
  <!-- 实体分类标签 -->
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

## 5. 数据导入导出 (脚本化)

### 5.1 批量导入脚本
```python
# scripts/import_tasks.py
import json
import requests
from pathlib import Path

def import_tasks_to_labelstudio(project_id, data_dir):
    """批量导入任务到Label Studio"""
    
    # Label Studio API配置
    api_url = "http://localhost:8080"
    api_token = "your_api_token"
    
    tasks = []
    for txt_file in Path(data_dir).glob("*.txt"):
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        task = {
            "data": {
                "ocr_content": content,
                "document_name": txt_file.name
            }
        }
        tasks.append(task)
    
    # 调用Label Studio API导入
    response = requests.post(
        f"{api_url}/api/projects/{project_id}/import",
        headers={"Authorization": f"Token {api_token}"},
        json=tasks
    )
    
    print(f"导入完成: {len(tasks)} 个任务")
```

### 5.2 结果导出脚本
```python
# scripts/export_results.py
import json
import requests
import csv

def export_annotations(project_id, output_file):
    """导出标注结果"""
    
    api_url = "http://localhost:8080"
    api_token = "your_api_token"
    
    # 获取标注结果
    response = requests.get(
        f"{api_url}/api/projects/{project_id}/export",
        headers={"Authorization": f"Token {api_token}"},
        params={"exportType": "JSON"}
    )
    
    annotations = response.json()
    
    # 转换为CSV格式
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Document', 'Entity', 'Label', 'Start', 'End'])
        
        for annotation in annotations:
            document = annotation['data']['document_name']
            for result in annotation.get('annotations', []):
                for entity in result.get('result', []):
                    writer.writerow([
                        document,
                        entity['value']['text'],
                        entity['value']['labels'][0],
                        entity['value']['start'],
                        entity['value']['end']
                    ])
    
    print(f"导出完成: {output_file}")
```

## 6. 部署方案 (极简)

### 6.1 开发环境 (本地)
```bash
# 1. 安装Label Studio
pip install label-studio

# 2. 启动服务
label-studio start --host 0.0.0.0 --port 8080

# 3. 创建项目并配置标注模板
# 通过Web界面操作

# 4. 导入数据
python scripts/import_tasks.py --project-id 1 --data-dir ./demo_data/

# 5. 开始标注工作
# 访问 http://localhost:8080

# 6. 导出结果
python scripts/export_results.py --project-id 1 --output results.csv
```

### 6.2 生产环境 (Docker可选)
```yaml
# docker-compose.yml (可选)
version: '3.8'
services:
  labelstudio:
    image: heartexlabs/label-studio:latest
    ports:
      - "8080:8080"
    environment:
      - LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
      - LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=/label-studio/data
    volumes:
      - ./data:/label-studio/data
      - ./media:/label-studio/media
      - ls_database:/label-studio/db
    command: label-studio start --host 0.0.0.0 --port 8080

volumes:
  ls_database:
```

## 7. 项目文件结构 (简化)

```
label-studio-document-ocr/
├── demo_data/                    # 示例数据
│   ├── document_ocr_demo_0.txt
│   ├── document_ocr_demo_1.txt
│   └── document_ocr_demo_2.txt
├── scripts/                     # 工具脚本
│   ├── import_tasks.py         # 批量导入
│   └── export_results.py       # 结果导出
├── configs/                     # 配置文件
│   └── entity_labeling_config.xml  # 标注模板
├── docker-compose.yml           # Docker部署(可选)
├── requirements.txt             # Python依赖
└── README.md                   # 部署说明
```

## 8. 快速开始指南

### 8.1 5分钟快速部署
```bash
# 克隆项目
git clone <repository>
cd label-studio-document-ocr

# 安装依赖
pip install -r requirements.txt

# 启动Label Studio
label-studio start

# 访问 http://localhost:8080
# 1. 创建项目
# 2. 导入标注模板 (configs/entity_labeling_config.xml)
# 3. 运行导入脚本导入demo数据
# 4. 开始标注
```

### 8.2 系统特点
- **零配置**: 开箱即用，无需复杂配置
- **轻量级**: 仅依赖Label Studio，无额外中间件
- **易扩展**: 基于脚本扩展，简单直接
- **易维护**: 最少的自定义代码，降低维护成本

## 9. 技术决策说明

### 9.1 为什么选择极简架构
1. **快速上线**: 避免过度工程化，专注核心功能
2. **降低成本**: 减少服务器资源消耗和维护成本
3. **易于Debug**: 架构简单，问题定位容易
4. **易于扩展**: 后续可根据实际需要渐进式扩展

### 9.2 何时考虑升级
- 并发用户 > 10人时，考虑添加Redis缓存
- 任务量 > 10万时，考虑添加任务队列
- 需要高可用时，考虑负载均衡和集群部署
- 需要复杂统计时，考虑添加数据分析模块

---

**说明**: 此版本专注于核心功能实现，确保项目快速启动和稳定运行。后续可根据实际使用情况逐步优化和扩展。