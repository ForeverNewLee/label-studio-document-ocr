# 数据库设计文档 (极简版)

## 1. 设计原则

### 1.1 核心原则
- **最小干预**: 完全使用Label Studio原生表结构
- **零扩展**: 不添加任何自定义表
- **数据驱动**: 通过数据字段而非数据库结构实现功能

### 1.2 设计策略
```
极简数据架构
├── Label Studio原生表 (完全保持)
│   ├── auth_user (用户表)
│   ├── project (项目表)  
│   ├── task (任务表)
│   └── annotation (标注表)
└── 无自定义扩展表
```

## 2. Label Studio原生表结构

### 2.1 核心表说明

#### 2.1.1 项目表 (project)
```sql
-- Label Studio原生项目表
project:
├── id (主键)
├── title (项目名称)
├── description (项目描述)
├── label_config (标注配置XML)
├── created_by_id (创建者)
├── created_at (创建时间)
└── organization_id (组织ID)
```

**存储敏感实体标注配置**:
- `label_config`: 存储敏感实体标注模板XML
- `description`: 存储项目说明和标注指导

#### 2.1.2 任务表 (task)  
```sql
-- Label Studio原生任务表
task:
├── id (主键)
├── data (JSON数据 - 核心字段)
├── project_id (项目ID)
├── created_at (创建时间)
├── updated_at (更新时间)
└── completed_at (完成时间)
```

**data字段结构** (存储所有业务数据):
```json
{
  "ocr_content": "From:\n[MASK_[MASK_Heather] [MASK_Hatfield]]\nINVOICE...",
  "document_name": "document_ocr_demo_0.txt",
  "meta": {
    "file_size": 1024,
    "import_batch": "batch_001", 
    "priority": "normal"
  }
}
```

#### 2.1.3 标注表 (annotation)
```sql
-- Label Studio原生标注表
annotation:
├── id (主键)
├── task_id (任务ID)
├── completed_by_id (标注员ID)
├── result (JSON结果 - 核心字段)
├── was_cancelled (是否取消)
├── created_at (创建时间)
└── updated_at (更新时间)
```

**result字段结构** (存储标注结果):
```json
[
  {
    "type": "labels",
    "value": {
      "start": 145,
      "end": 152,
      "text": "Heather",
      "labels": ["FirstName"]
    }
  },
  {
    "type": "labels", 
    "value": {
      "start": 153,
      "end": 162,
      "text": "Hatfield",
      "labels": ["LastName"]
    }
  }
]
```

## 3. 数据使用策略

### 3.1 批量导入实现
```python
# 通过data字段实现批量导入
def import_task(project_id, ocr_file_path):
    """导入单个OCR文档"""
    
    with open(ocr_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    task_data = {
        "ocr_content": content,
        "document_name": os.path.basename(ocr_file_path),
        "meta": {
            "import_time": datetime.now().isoformat(),
            "file_size": len(content),
            "import_batch": "demo_batch"
        }
    }
    
    # 调用Label Studio API
    response = requests.post(
        f"{api_url}/api/projects/{project_id}/import",
        headers={"Authorization": f"Token {api_token}"},
        json=[{"data": task_data}]
    )
```

### 3.2 结果统计实现
```python
# 通过查询原生表实现统计
def get_annotation_stats(project_id):
    """获取标注统计"""
    
    # 查询任务总数
    tasks = requests.get(
        f"{api_url}/api/projects/{project_id}/tasks",
        headers={"Authorization": f"Token {api_token}"}
    ).json()
    
    # 查询标注结果
    annotations = requests.get(
        f"{api_url}/api/projects/{project_id}/export",
        headers={"Authorization": f"Token {api_token}"}
    ).json()
    
    # 统计计算
    total_tasks = len(tasks)
    completed_tasks = len([a for a in annotations if a.get('annotations')])
    total_entities = sum(len(ann.get('result', [])) 
                        for a in annotations 
                        for ann in a.get('annotations', []))
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
        "total_entities": total_entities
    }
```

## 4. 质量控制实现

### 4.1 通过Label Studio内置功能
```python
# 使用Label Studio原生审核功能
def setup_review_process(project_id):
    """配置审核流程"""
    
    project_settings = {
        "maximum_annotations": 1,        # 每个任务最多1个标注
        "show_annotation_history": True,  # 显示标注历史
        "show_overlap_first": True,       # 优先显示重叠标注
        "overlap_cohort_percentage": 10,  # 10%的任务用于质量检查
    }
    
    # 更新项目设置
    response = requests.patch(
        f"{api_url}/api/projects/{project_id}",
        headers={"Authorization": f"Token {api_token}"},
        json=project_settings
    )
```

### 4.2 审核员角色配置
```python
# 通过Label Studio用户角色实现审核
def assign_reviewer_role(user_id, project_id):
    """分配审核员角色"""
    
    # Label Studio内置角色管理
    # 通过Web界面或API分配用户角色
    # - Annotator: 标注员
    # - Reviewer: 审核员  
    # - Manager: 项目管理员
```

## 5. 数据导出格式

### 5.1 标准导出格式
```json
// Label Studio标准导出格式
{
  "id": 1,
  "data": {
    "ocr_content": "From:\n[MASK_[MASK_Heather] [MASK_Hatfield]]...",
    "document_name": "document_ocr_demo_0.txt"
  },
  "annotations": [
    {
      "id": 1,
      "completed_by": 1,
      "result": [
        {
          "type": "labels",
          "value": {
            "start": 145,
            "end": 152, 
            "text": "Heather",
            "labels": ["FirstName"]
          }
        }
      ],
      "was_cancelled": false,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 5.2 CSV导出格式
```csv
Document,Entity_Text,Entity_Label,Start_Pos,End_Pos,Annotator,Created_At
document_ocr_demo_0.txt,Heather,FirstName,145,152,user1,2024-01-15T10:30:00Z
document_ocr_demo_0.txt,Hatfield,LastName,153,162,user1,2024-01-15T10:30:00Z
```

## 6. 备份和恢复

### 6.1 数据备份
```bash
# SQLite备份 (开发环境)
cp ~/.local/share/label-studio/label_studio.sqlite3 backup_$(date +%Y%m%d).sqlite3

# PostgreSQL备份 (生产环境)
pg_dump labelstudio_db > backup_$(date +%Y%m%d).sql
```

### 6.2 数据恢复
```bash
# SQLite恢复
cp backup_20240115.sqlite3 ~/.local/share/label-studio/label_studio.sqlite3

# PostgreSQL恢复
psql labelstudio_db < backup_20240115.sql
```

## 7. 性能优化

### 7.1 Label Studio内置优化
- 使用PostgreSQL替代SQLite (生产环境)
- 开启Label Studio缓存机制
- 合理设置分页大小

### 7.2 查询优化
```python
# 分页查询大量任务
def get_tasks_paginated(project_id, page=1, page_size=50):
    """分页获取任务"""
    
    response = requests.get(
        f"{api_url}/api/projects/{project_id}/tasks",
        headers={"Authorization": f"Token {api_token}"},
        params={
            "page": page,
            "page_size": page_size
        }
    )
    return response.json()
```

## 8. 监控和维护

### 8.1 数据库监控
```python
# 通过Label Studio API监控数据库状态
def check_database_health():
    """检查数据库健康状态"""
    
    try:
        # 测试API连接
        response = requests.get(
            f"{api_url}/api/projects",
            headers={"Authorization": f"Token {api_token}"}
        )
        
        if response.status_code == 200:
            return {"status": "healthy", "projects": len(response.json())}
        else:
            return {"status": "unhealthy", "error": response.text}
            
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

### 8.2 清理维护
```python
# 清理已完成的任务 (可选)
def cleanup_completed_tasks(project_id, days_old=30):
    """清理指定天数前的已完成任务"""
    
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    # 获取已完成的旧任务
    tasks = requests.get(
        f"{api_url}/api/projects/{project_id}/tasks",
        headers={"Authorization": f"Token {api_token}"},
        params={"completed_before": cutoff_date.isoformat()}
    ).json()
    
    # 根据需要删除或归档
    print(f"发现 {len(tasks)} 个可清理的任务")
```

## 9. 迁移策略

### 9.1 数据迁移
如果将来需要扩展数据库，可以：

1. **导出现有数据**
```python
# 导出所有项目数据
def export_all_data():
    projects = get_all_projects()
    for project in projects:
        export_project_data(project['id'])
```

2. **数据格式转换**
```python
# 将Label Studio数据转换为其他格式
def convert_to_training_format(annotations):
    training_data = []
    for ann in annotations:
        # 转换为训练数据格式
        pass
    return training_data
```

## 10. 设计优势

### 10.1 极简优势
- **零维护成本**: 无自定义表，无数据迁移风险
- **完全兼容**: 与Label Studio完全兼容
- **快速部署**: 无需数据库初始化脚本
- **易于升级**: Label Studio升级无障碍

### 10.2 扩展能力
如果将来需要更复杂的功能：
- 可以渐进式添加扩展表
- 通过JSON字段扩展数据结构
- 保持向后兼容性

---

**总结**: 此设计完全依赖Label Studio原生能力，通过合理使用JSON字段和API实现所有业务需求，确保系统的简单性和可维护性。