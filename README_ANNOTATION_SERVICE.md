# 敏感实体标注服务

基于Label Studio的英文票据OCR敏感实体识别和分类标注平台。

## 📋 项目概述

本项目提供一个专业的敏感实体标注平台，用于处理2万张英文票据图片的OCR结果，进行敏感实体识别和类别标注，支持数据脱敏和隐私保护模型训练。

### 核心特性

- **🎯 专业化标注**: 针对敏感信息识别优化的标注界面
- **⚡ 极简架构**: 3分钟部署，零维护成本
- **🔧 完全配置化**: 无需编程，通过配置实现定制
- **📊 多格式导出**: 支持CSV、JSON、实体清单等多种导出格式
- **🚀 批量处理**: 支持2万级别任务的批量导入和处理

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Label Studio 1.9.0+

### 一键安装和启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python scripts/start_service.py
```

启动后访问 http://localhost:8080 完成初始设置。

### 完整配置流程

```bash
# 1. 创建标注项目
python scripts/setup_project.py --api-token YOUR_TOKEN --project-name "敏感实体标注"

# 2. 导入demo数据
python scripts/import_ocr_documents.py --api-token YOUR_TOKEN --project-id PROJECT_ID

# 3. 开始标注工作
# 访问项目页面进行标注

# 4. 导出标注结果
python scripts/export_annotations.py --api-token YOUR_TOKEN --project-id PROJECT_ID
```

## 📁 项目结构

```
├── scripts/                    # 核心脚本
│   ├── start_service.py        # 一键启动服务
│   ├── setup_project.py        # 项目创建和配置
│   ├── import_ocr_documents.py # 批量数据导入
│   └── export_annotations.py   # 标注结果导出
├── configs/                    # 配置文件
│   └── annotation_template.xml # 标注界面模板
├── demo_data/                  # 示例数据
│   ├── document_ocr_demo_0.txt # 发票示例
│   ├── document_ocr_demo_1.txt # 工资单示例
│   └── document_ocr_demo_2.txt # 收据示例
├── exports/                    # 导出结果目录
├── docs/                       # 详细文档
│   ├── requirements/           # 需求文档
│   ├── product_design/         # 产品设计
│   └── technical/              # 技术文档
└── requirements.txt            # Python依赖
```

## 🏷️ 标注类别体系

### 主要类别 (4大类)

1. **人名相关**: FullName, FirstName, LastName
2. **地址相关**: Address, StreetNumber, StreetName, City, State, ZipCode  
3. **证件号码**: InvoiceNumber, CompanyName, CheckNumber
4. **时间和联系信息**: Date, MilitaryAddress

### 快捷键

- **1-9**: 人名和地址相关标签
- **q,w,e,r,t**: 证件号码和时间相关标签

## 📊 使用流程

### 1. 服务启动

```bash
python scripts/start_service.py
```

### 2. 项目创建

```bash
python scripts/setup_project.py \
    --api-token YOUR_TOKEN \
    --project-name "敏感实体标注项目"
```

### 3. 数据导入

```bash
python scripts/import_ocr_documents.py \
    --api-token YOUR_TOKEN \
    --project-id PROJECT_ID \
    --data-dir ./demo_data
```

### 4. 标注工作

1. 访问项目页面: http://localhost:8080/projects/PROJECT_ID/
2. 选择任务开始标注
3. 使用鼠标选择文本，按快捷键分类
4. 提交标注结果

### 5. 结果导出

```bash
# 导出多种格式
python scripts/export_annotations.py \
    --api-token YOUR_TOKEN \
    --project-id PROJECT_ID \
    --format csv,json,entity_list,statistics
```

## 🔧 配置说明

### 标注模板定制

编辑 `configs/annotation_template.xml` 可以定制：
- 标注界面布局
- 实体类别和颜色
- 快捷键配置
- 界面文本和说明

### 环境变量

可通过环境变量配置Label Studio：

```bash
export LABEL_STUDIO_HOST=0.0.0.0
export LABEL_STUDIO_PORT=8080
export LABEL_STUDIO_DATABASE_NAME=label_studio.sqlite3
```

## 📈 性能特性

- **极速部署**: 3分钟从安装到可用
- **批量处理**: 支持2万个任务批量导入
- **并发标注**: 支持多用户同时标注
- **实时同步**: 标注结果实时保存
- **格式导出**: 多种格式一键导出

## 🛠️ 开发与定制

### 代码质量

项目使用现代Python开发标准：

```bash
# 代码格式检查
ruff check scripts/

# 类型检查
mypy scripts/
```

### 扩展开发

基于极简架构原则，所有定制通过以下方式实现：
- 标注模板配置 (XML)
- API脚本调用 (Python)
- 配置文件修改 (JSON/XML)

## 📚 文档资源

- [需求文档](docs/requirements/): 详细需求说明和业务流程
- [产品设计](docs/product_design/): 用户界面和产品设计
- [技术文档](docs/technical/): 架构设计和部署指南
- [标注示例](docs/product_design/annotation_examples.md): 详细标注示例和操作指南

## 🤝 支持与反馈

### 常见问题

1. **服务启动失败**: 检查端口占用和Python版本
2. **API连接失败**: 确认Token正确性和网络连接
3. **导入数据失败**: 检查文件格式和权限设置

### 技术支持

- 查看详细文档: [docs/technical/](docs/technical/)
- 参考标注示例: [docs/product_design/annotation_examples.md](docs/product_design/annotation_examples.md)

## 📄 开源协议

本项目基于Label Studio开源版本构建，遵循Apache 2.0协议。

---

**快速链接**: [技术文档](docs/technical/) | [产品设计](docs/product_design/) | [标注示例](docs/product_design/annotation_examples.md) 