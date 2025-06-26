# Label Studio定制化方案 (极简版)

## 1. 定制化策略

### 1.1 核心原则
- **配置优先**: 仅通过配置文件实现定制，零代码开发
- **模板驱动**: 通过标注模板实现专业化界面
- **API调用**: 通过现有API实现所有扩展功能
- **脚本辅助**: 使用Python脚本实现批量操作

### 1.2 定制范围
```
Label Studio Core (完全使用)
├── 用户管理 ✓
├── 项目管理 ✓  
├── 任务管理 ✓
├── 基础标注界面 ✓
└── API接口 ✓

极简扩展 (配置实现)
├── 敏感实体标注模板
├── 批量导入脚本
└── 结果导出脚本
```

## 2. 标注模板配置 (核心)

### 2.1 敏感实体NER模板
```xml
<View>
  <!-- 任务说明 -->
  <Header value="敏感实体标注任务"/>
  <Text value="请识别文档中的所有敏感实体并进行分类标注，包括被[MASK]遮挡的敏感信息"/>
  
  <!-- 文档内容显示 -->
  <Text name="text" value="$ocr_content" 
        style="white-space: pre-wrap; font-family: monospace; border: 1px solid #ddd; padding: 15px; background: #f9f9f9;"/>

  <!-- 实体分类标签 -->
  <Labels name="entity_type" toName="text">
    <!-- 人名相关 (红色系) -->
    <Label value="FullName" background="#dc3545" hotkey="1"/>
    <Label value="FirstName" background="#c82333" hotkey="2"/>  
    <Label value="LastName" background="#e85563" hotkey="3"/>
    
    <!-- 地址相关 (蓝色系) -->
    <Label value="Address" background="#007bff" hotkey="4"/>
    <Label value="StreetNumber" background="#0056b3" hotkey="5"/>
    <Label value="StreetName" background="#3395ff" hotkey="6"/>
    <Label value="City" background="#004085" hotkey="7"/>
    <Label value="State" background="#66b5ff" hotkey="8"/>
    <Label value="ZipCode" background="#1a88ff" hotkey="9"/>
    
    <!-- 证件号码 (绿色系) -->
    <Label value="InvoiceNumber" background="#28a745" hotkey="q"/>
    <Label value="CompanyName" background="#1e7e34" hotkey="w"/>
    <Label value="CheckNumber" background="#5cb85c" hotkey="e"/>
    
    <!-- 时间信息 (橙色/紫色) -->
    <Label value="Date" background="#fd7e14" hotkey="r"/>
    <Label value="MilitaryAddress" background="#6f42c1" hotkey="t"/>
  </Labels>

  <!-- 快捷键说明 -->
  <Text value="快捷键: 1-9(人名地址) | q,w,e(证件) | r,t(时间军址)" 
        style="font-size: 12px; color: #666; margin-top: 10px;"/>
</View>
```

### 2.2 模板使用方法
1. **创建项目时**: 将上述XML复制到Label Studio项目的"Labeling Interface"配置中
2. **项目设置**: 配置任务分发和审核规则
3. **用户培训**: 向标注员说明快捷键和标注规范

## 3. 批量导入脚本

### 3.1 简化导入脚本
```python
#!/usr/bin/env python3
# scripts/import_ocr_documents.py

import requests
import json
from pathlib import Path
import argparse

def import_documents(api_url, api_token, project_id, data_dir):
    """批量导入OCR文档"""
    
    print(f"🚀 开始导入OCR文档到项目 {project_id}")
    
    # 准备任务数据
    tasks = []
    for txt_file in Path(data_dir).glob("*.txt"):
        print(f"📄 读取文件: {txt_file.name}")
        
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 创建任务数据
        task = {
            "data": {
                "ocr_content": content,
                "document_name": txt_file.name
            }
        }
        tasks.append(task)
    
    if not tasks:
        print("❌ 没有找到txt文件")
        return
    
    # 批量导入
    print(f"📤 导入 {len(tasks)} 个文档...")
    response = requests.post(
        f"{api_url}/api/projects/{project_id}/import",
        headers={
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        },
        json=tasks
    )
    
    if response.status_code == 201:
        print(f"✅ 成功导入 {len(tasks)} 个文档")
    else:
        print(f"❌ 导入失败: {response.status_code} - {response.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='批量导入OCR文档')
    parser.add_argument('--api-url', default='http://localhost:8080')
    parser.add_argument('--api-token', required=True)
    parser.add_argument('--project-id', required=True, type=int)
    parser.add_argument('--data-dir', default='./demo_data')
    
    args = parser.parse_args()
    import_documents(args.api_url, args.api_token, args.project_id, args.data_dir)
```

### 3.2 使用方法
```bash
# 获取API Token: Label Studio界面 -> Account -> Access Token
python scripts/import_ocr_documents.py \
    --api-token "你的API_TOKEN" \
    --project-id 1 \
    --data-dir ./demo_data/
```

## 4. 结果导出脚本

### 4.1 简化导出脚本
```python
#!/usr/bin/env python3
# scripts/export_annotations.py

import requests
import csv
import json
from datetime import datetime
import argparse

def export_annotations(api_url, api_token, project_id, output_format='csv'):
    """导出标注结果"""
    
    print(f"📥 从项目 {project_id} 导出标注结果...")
    
    # 获取完整的标注数据
    response = requests.get(
        f"{api_url}/api/projects/{project_id}/export",
        headers={"Authorization": f"Token {api_token}"},
        params={"exportType": "JSON"}
    )
    
    if response.status_code != 200:
        print(f"❌ 导出失败: {response.status_code} - {response.text}")
        return
    
    data = response.json()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if output_format == 'csv':
        # 导出为CSV格式
        output_file = f"annotations_export_{timestamp}.csv"
        export_to_csv(data, output_file)
    else:
        # 导出为JSON格式
        output_file = f"annotations_export_{timestamp}.json"
        export_to_json(data, output_file)
    
    print(f"✅ 导出完成: {output_file}")

def export_to_csv(data, output_file):
    """导出为CSV格式"""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Document', 'Entity_Text', 'Entity_Label', 'Start_Pos', 'End_Pos', 'Annotator', 'Created_At'])
        
        for item in data:
            document = item['data'].get('document_name', 'unknown')
            
            for annotation in item.get('annotations', []):
                annotator = annotation.get('completed_by', 'unknown')
                created_at = annotation.get('created_at', '')
                
                for result in annotation.get('result', []):
                    if result.get('type') == 'labels':
                        writer.writerow([
                            document,
                            result['value']['text'],
                            result['value']['labels'][0] if result['value']['labels'] else '',
                            result['value']['start'],
                            result['value']['end'],
                            annotator,
                            created_at
                        ])

def export_to_json(data, output_file):
    """导出为JSON格式"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='导出标注结果')
    parser.add_argument('--api-url', default='http://localhost:8080')
    parser.add_argument('--api-token', required=True)
    parser.add_argument('--project-id', required=True, type=int)
    parser.add_argument('--format', choices=['csv', 'json'], default='csv')
    
    args = parser.parse_args()
    export_annotations(args.api_url, args.api_token, args.project_id, args.format)
```

## 5. Label Studio配置优化

### 5.1 项目设置推荐
```json
{
  "title": "敏感实体标注项目",
  "description": "英文票据OCR文档敏感实体识别与分类标注",
  "label_config": "<!-- 上面的XML模板 -->",
  "maximum_annotations": 1,
  "show_annotation_history": true,
  "show_overlap_first": true,
  "overlap_cohort_percentage": 10,
  "show_skip_button": true,
  "show_submit_button": true,
  "show_hotkeys_help": true,
  "enable_empty_annotation": false
}
```

### 5.2 质量控制设置
```json
{
  "review_settings": {
    "require_review": false,
    "review_percentage": 10,
    "auto_accept_predictions": false
  },
  "annotation_settings": {
    "show_labels_hotkey_help": true,
    "preserve_selected_tool": true,
    "select_unlabeled_first": true
  }
}
```

## 6. 用户角色管理

### 6.1 通过Web界面设置
1. **管理员**: 创建项目、管理用户、导入数据
2. **标注员**: 执行标注任务
3. **审核员**: 质量审核（可选）

### 6.2 权限控制
- 使用Label Studio内置的用户权限系统
- 不需要自定义权限模块
- 通过项目成员管理实现访问控制

## 7. 监控和统计

### 7.1 通过Label Studio界面
- **项目概览**: 任务进度、完成情况
- **用户统计**: 标注员工作量统计
- **质量指标**: 通过审核功能查看质量

### 7.2 简单统计脚本
```python
# scripts/get_stats.py
def get_project_stats(api_url, api_token, project_id):
    """获取项目统计信息"""
    
    # 获取任务统计
    tasks_response = requests.get(
        f"{api_url}/api/projects/{project_id}/tasks",
        headers={"Authorization": f"Token {api_token}"}
    )
    tasks = tasks_response.json()
    
    # 获取标注统计
    annotations_response = requests.get(
        f"{api_url}/api/projects/{project_id}/export",
        headers={"Authorization": f"Token {api_token}"}
    )
    annotations = annotations_response.json()
    
    # 计算统计指标
    total_tasks = len(tasks)
    completed_tasks = len([a for a in annotations if a.get('annotations')])
    completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
    
    print(f"📊 项目统计:")
    print(f"   总任务数: {total_tasks}")
    print(f"   已完成: {completed_tasks}")
    print(f"   完成率: {completion_rate:.1%}")
```

## 8. 部署和维护

### 8.1 配置文件管理
```
configs/
├── entity_labeling_config.xml    # 标注模板
├── project_settings.json         # 项目设置
└── user_guide.md                 # 用户使用指南
```

### 8.2 脚本工具
```
scripts/
├── import_ocr_documents.py       # 批量导入
├── export_annotations.py         # 结果导出
├── get_stats.py                  # 统计信息
└── backup_project.py             # 项目备份
```

## 9. 最佳实践

### 9.1 标注规范
1. **一致性**: 相同类型实体使用相同标签
2. **完整性**: 不遗漏任何敏感实体
3. **准确性**: 确保标注边界准确

### 9.2 质量保证
1. **培训**: 标注员培训和测试
2. **抽检**: 定期质量抽检
3. **反馈**: 及时纠错和改进

### 9.3 效率提升
1. **快捷键**: 充分利用快捷键操作
2. **批处理**: 合理安排批量操作
3. **模板**: 使用标准化的标注模板

## 10. 扩展可能

### 10.1 如需更多功能
- **预标注**: 集成NLP模型进行预标注
- **主动学习**: 基于已标注数据优化工作流
- **质量控制**: 更复杂的多轮审核机制
- **统计分析**: 更详细的数据分析和报表

### 10.2 渐进式升级
当前极简方案作为起点，可根据实际需求渐进式添加功能：
1. 先使用基础功能验证流程
2. 根据使用反馈识别改进点
3. 渐进式添加高级功能
4. 保持系统简洁性

---

**总结**: 此方案完全基于Label Studio原生能力，通过配置和脚本实现所有必要功能，确保系统简单、可靠、易维护。 