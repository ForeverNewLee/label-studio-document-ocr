# 🚀 敏感实体标注服务 - 快速启动指南

## 一键启动 (3分钟完成)

### 步骤1: 启动服务
```bash
# 安装依赖并启动
pip install -r requirements.txt
python3 scripts/start_service.py
```

### 步骤2: 初始设置
1. 访问 http://localhost:8080
2. 创建管理员账户
3. 登录后获取API Token: Account & Settings → Access Token

### 步骤3: 创建项目
```bash
python3 scripts/setup_project.py --api-token YOUR_TOKEN
```

### 步骤4: 导入数据
```bash
python3 scripts/import_ocr_documents.py --api-token YOUR_TOKEN --project-id PROJECT_ID
```

### 步骤5: 开始标注
- 访问项目页面开始标注
- 使用快捷键 1-9, q,w,e,r,t 快速分类

### 步骤6: 导出结果
```bash
python3 scripts/export_annotations.py --api-token YOUR_TOKEN --project-id PROJECT_ID
```

## 🎯 标注快捷键

| 快捷键 | 实体类型 | 示例 |
|--------|----------|------|
| 1 | FullName | John Smith |
| 2 | FirstName | John |
| 3 | LastName | Smith |
| 4 | Address | 123 Main St |
| 5 | StreetNumber | 123 |
| 6 | StreetName | Main St |
| 7 | City | New York |
| 8 | State | NY |
| 9 | ZipCode | 10001 |
| q | InvoiceNumber | T96087065 |
| w | CompanyName | ABC Corp |
| e | CheckNumber | 001234 |
| r | Date | 05/06/2022 |
| t | MilitaryAddress | FPO AE |

## 📋 Demo数据

项目包含3个示例文档：
- `demo_data/document_ocr_demo_0.txt` - 发票示例
- `demo_data/document_ocr_demo_1.txt` - 工资单示例
- `demo_data/document_ocr_demo_2.txt` - 收据示例

## 🛠️ 故障排除

### 常见问题

**服务启动失败**
```bash
# 检查环境
python3 scripts/validate_setup.py
```

**端口被占用**
```bash
# 使用其他端口
python3 scripts/start_service.py --port 8090
```

**API连接失败**
- 确认服务正在运行
- 检查API Token是否正确
- 确认项目ID存在

## 📚 完整文档

- [详细说明](README_ANNOTATION_SERVICE.md)
- [技术文档](docs/technical/)
- [标注示例](docs/product_design/annotation_examples.md)

---

**🎉 开始标注吧！** 如有问题请查看完整文档或运行验证脚本。 