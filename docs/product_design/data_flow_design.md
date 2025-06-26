# 数据流程设计

## 1. 数据流程概览

### 1.1 整体数据流向
```
OCR原始数据 → 任务创建 → 标注执行 → 质量检查 → 审核确认 → 结果导出
     ↓          ↓         ↓         ↓         ↓         ↓
   文本文件   任务队列   标注数据   质量报告   最终数据   导出文件
```

### 1.2 核心数据实体
- **原始文档**: OCR处理后的文本数据
- **标注任务**: 包含文档内容和标注要求的工作单元
- **标注结果**: 用户标注的实体和分类数据
- **质量数据**: 审核、校验和统计信息
- **导出数据**: 格式化的最终标注结果

## 2. 任务管理数据流

### 2.1 任务创建流程
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  OCR文本     │──▶ │  任务生成    │──▶ │  任务队列    │
│  文件批量    │    │  引擎       │    │  存储       │
└─────────────┘    └─────────────┘    └─────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
  │ 文件验证     │    │ 元数据提取   │    │ 状态初始化   │
  │ 格式检查     │    │ 任务配置     │    │ 分配准备     │
  └─────────────┘    └─────────────┘    └─────────────┘
```

#### 2.1.1 输入数据格式
```json
{
  "task_id": "task_001",
  "document_name": "invoice_001.txt",
  "ocr_content": "From:\n[MASK_[MASK_Heather] [MASK_Hatfield]]\nINVOICE\n\nBusiness Name:\n[MASK_[MASK_Heather] [MASK_Hatfield]]\n[MASK_[MASK_36441] [MASK_Phillips Underpass] Suite 106]\n[MASK_New Daniel], [MASK_MT] [MASK_49458]\n\nINVOICE #\nT96087065\n\nBill to:\nWilson, Taylor and Kim and Sons",
  "instruction": "找出文档中没有被[MASK]框住的实体，将你找到的实体加入清单，并补全/检查清单中的实体类别",
  "entity_categories": ["人名、人名缩写、姓、名", "地址、街道名、街道号、邮编、国家、美国的州、城市", "护照号、身份证号、驾照号、银行账号、卡号", "时间戳、出生日期、ip地址、硬件地址"],
  "priority": "normal",
  "estimated_time": 15
}
```

#### 2.1.2 任务状态流转
```
创建 → 待分配 → 已分配 → 标注中 → 待审核 → 审核中 → 已完成
  ↓       ↓       ↓       ↓       ↓       ↓       ↓
初始   队列中   分配给   进行中   等待    审核    完成
状态   等待     标注员   标注    审核    过程    归档
```

### 2.2 任务分配逻辑
```python
# 任务分配策略
def assign_task_strategy():
    factors = {
        "annotator_workload": 0.4,      # 标注员当前工作量
        "skill_match": 0.3,             # 技能匹配度
        "historical_performance": 0.2,   # 历史表现
        "task_priority": 0.1            # 任务优先级
    }
    return weighted_assignment(factors)
```

## 3. 标注数据流

### 3.1 标注执行流程
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  任务加载    │──▶ │  实体识别    │──▶ │  分类标注    │
│  文档展示    │    │  文本选择    │    │  类别分配    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
  │ 界面渲染     │    │ 选择验证     │    │ 实时保存     │
  │ 指令显示     │    │ 高亮显示     │    │ 状态更新     │
  └─────────────┘    └─────────────┘    └─────────────┘
```

#### 3.1.1 标注数据结构
```json
{
  "annotation_id": "ann_001_001",
  "task_id": "task_001",
  "annotator_id": "user_001",
  "entities": [
    {
      "text": "Heather Hatfield",
      "start_pos": 15,
      "end_pos": 30,
      "category": "FullName",
      "confidence": 0.95,
      "timestamp": "2024-12-28T10:30:00Z"
    },
    {
      "text": "Wilson, Taylor and Kim and Sons",
      "start_pos": 250,
      "end_pos": 281,
      "category": "CompanyName",
      "confidence": 0.98,
      "timestamp": "2024-12-28T10:32:00Z"
    },
    {
      "text": "T96087065",
      "start_pos": 180,
      "end_pos": 189,
      "category": "InvoiceNumber",
      "confidence": 0.99,
      "timestamp": "2024-12-28T10:33:00Z"
    }
  ],
  "status": "in_progress",
  "save_time": "2024-12-28T10:35:00Z"
}
```

#### 3.1.2 实时保存机制
```python
# 自动保存策略
def auto_save_strategy():
    triggers = [
        "entity_added",      # 添加实体时
        "entity_modified",   # 修改实体时
        "category_changed",  # 改变分类时
        "interval_30s"       # 30秒定时保存
    ]
    return continuous_save(triggers)
```

### 3.2 标注校验规则
```python
validation_rules = {
    "entity_completeness": {
        "description": "实体文本不能为空",
        "rule": "entity.text.strip() != ''"
    },
    "category_validity": {
        "description": "分类必须在预定义列表中",
        "rule": "entity.category in VALID_CATEGORIES"
    },
    "position_accuracy": {
        "description": "位置信息必须准确",
        "rule": "0 <= entity.start_pos < entity.end_pos <= document.length"
    },
    "duplicate_detection": {
        "description": "检测重复标注",
        "rule": "no_overlapping_entities(entities)"
    }
}
```

## 4. 质量控制数据流

### 4.1 质量检查流程
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  标注完成    │──▶ │  自动校验    │──▶ │  质量评估    │
│  提交审核    │    │  规则检查    │    │  分数计算    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
  │ 状态更新     │    │ 错误标记     │    │ 审核队列     │
  │ 通知发送     │    │ 反馈生成     │    │ 优先排序     │
  └─────────────┘    └─────────────┘    └─────────────┘
```

#### 4.1.1 质量评估指标
```json
{
  "quality_metrics": {
    "completeness": {
      "score": 0.95,
      "description": "标注完整度",
      "calculation": "labeled_entities / total_entities"
    },
    "accuracy": {
      "score": 0.92,
      "description": "分类准确性",
      "calculation": "correct_categories / total_categories"
    },
    "consistency": {
      "score": 0.88,
      "description": "标注一致性",
      "calculation": "consistent_annotations / total_comparisons"
    },
    "efficiency": {
      "score": 0.90,
      "description": "标注效率",
      "calculation": "completed_tasks / assigned_time"
    }
  }
}
```

#### 4.1.2 异常检测规则
```python
anomaly_detection = {
    "speed_anomaly": {
        "condition": "completion_time < expected_time * 0.3",
        "action": "flag_for_review",
        "severity": "medium"
    },
    "quality_drop": {
        "condition": "accuracy_score < user_avg * 0.8",
        "action": "require_additional_review",
        "severity": "high"
    },
    "consistency_issue": {
        "condition": "consistency_score < 0.7",
        "action": "provide_feedback_training",
        "severity": "medium"
    }
}
```

### 4.2 审核流程
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  审核队列    │──▶ │  人工审核    │──▶ │  反馈处理    │
│  任务分配    │    │  结果验证    │    │  状态更新    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
  │ 优先级排序   │    │ 修改建议     │    │ 数据归档     │
  │ 审核员分配   │    │ 质量记录     │    │ 统计更新     │
  └─────────────┘    └─────────────┘    └─────────────┘
```

## 5. 数据导出流程

### 5.1 导出处理流程
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  导出请求    │──▶ │  数据筛选    │──▶ │  格式转换    │
│  参数配置    │    │  质量过滤    │    │  文件生成    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
  │ 权限验证     │    │ 数据聚合     │    │ 下载链接     │
  │ 范围检查     │    │ 统计计算     │    │ 通知发送     │
  └─────────────┘    └─────────────┘    └─────────────┘
```

#### 5.1.1 导出数据格式
```json
{
  "export_metadata": {
    "export_id": "exp_20241228_001",
    "export_time": "2024-12-28T15:30:00Z",
    "total_tasks": 1000,
    "total_entities": 15420,
    "quality_threshold": 0.95
  },
  "annotations": [
    {
      "task_id": "task_001",
      "document_name": "invoice_001.txt",
      "entities": [
        {
          "text": "Heather Hatfield",
          "category": "FullName",
          "position": {"start": 15, "end": 30},
          "confidence": 0.95
        }
      ],
      "annotator": "user_001",
      "review_status": "approved",
      "quality_score": 0.96
    }
  ]
}
```

#### 5.1.2 导出格式配置
```python
export_formats = {
    "standard": {
        "description": "标准格式 (实体:标签)",
        "format": "text",
        "template": "{entity_text}: {category}"
    },
    "json": {
        "description": "JSON格式",
        "format": "json",
        "structure": "hierarchical"
    },
    "csv": {
        "description": "CSV格式",
        "format": "csv",
        "columns": ["task_id", "entity_text", "category", "start_pos", "end_pos"]
    },
    "xml": {
        "description": "XML格式",
        "format": "xml",
        "schema": "annotation_schema.xsd"
    }
}
```

## 6. 数据存储设计

### 6.1 数据库结构
```sql
-- 任务表
CREATE TABLE tasks (
    id VARCHAR(50) PRIMARY KEY,
    document_name VARCHAR(255),
    ocr_content TEXT,
    status VARCHAR(20),
    assigned_to VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 标注表
CREATE TABLE annotations (
    id VARCHAR(50) PRIMARY KEY,
    task_id VARCHAR(50),
    entity_text VARCHAR(500),
    category VARCHAR(50),
    start_position INT,
    end_position INT,
    annotator_id VARCHAR(50),
    confidence DECIMAL(3,2),
    created_at TIMESTAMP
);

-- 审核表
CREATE TABLE reviews (
    id VARCHAR(50) PRIMARY KEY,
    annotation_id VARCHAR(50),
    reviewer_id VARCHAR(50),
    status VARCHAR(20),
    feedback TEXT,
    quality_score DECIMAL(3,2),
    reviewed_at TIMESTAMP
);

-- 质量统计表
CREATE TABLE quality_metrics (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50),
    metric_type VARCHAR(50),
    metric_value DECIMAL(5,2),
    calculation_date DATE
);
```

### 6.2 数据备份策略
```python
backup_strategy = {
    "frequency": {
        "incremental": "every_hour",      # 增量备份
        "full": "daily_at_2am",          # 全量备份
        "archive": "weekly_sunday"        # 归档备份
    },
    "retention": {
        "daily_backups": "30_days",
        "weekly_backups": "12_weeks",
        "monthly_backups": "12_months"
    },
    "verification": {
        "integrity_check": "daily",
        "restore_test": "monthly"
    }
}
```

## 7. 数据安全与隐私

### 7.1 敏感数据处理
```python
data_security_measures = {
    "encryption": {
        "data_at_rest": "AES-256",
        "data_in_transit": "TLS 1.3",
        "key_management": "HSM"
    },
    "access_control": {
        "authentication": "multi_factor",
        "authorization": "role_based",
        "audit_logging": "comprehensive"
    },
    "data_masking": {
        "development_env": "full_masking",
        "testing_env": "partial_masking",
        "analytics": "aggregated_only"
    }
}
```

### 7.2 数据生命周期管理
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  数据创建    │──▶ │  活跃使用    │──▶ │  归档存储    │
│  标注录入    │    │  标注处理    │    │  长期保存    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
  │ 质量检查     │    │ 访问监控     │    │ 定期清理     │
  │ 格式验证     │    │ 使用统计     │    │ 安全销毁     │
  └─────────────┘    └─────────────┘    └─────────────┘
```

## 8. 性能优化

### 8.1 数据流优化策略
```python
performance_optimizations = {
    "caching": {
        "frequently_accessed_tasks": "redis_cache",
        "user_preferences": "session_cache",
        "entity_categories": "memory_cache"
    },
    "batch_processing": {
        "task_creation": "batch_size_100",
        "annotation_save": "bulk_insert",
        "quality_calculation": "background_job"
    },
    "indexing": {
        "task_queries": "composite_index",
        "annotation_search": "full_text_index",
        "user_performance": "partial_index"
    }
}
```

### 8.2 监控与告警
```python
monitoring_metrics = {
    "data_flow_health": {
        "task_processing_rate": "tasks_per_minute",
        "annotation_save_latency": "milliseconds",
        "export_generation_time": "seconds"
    },
    "system_performance": {
        "database_connection_pool": "active_connections",
        "memory_usage": "percentage",
        "disk_space": "available_gb"
    },
    "business_metrics": {
        "daily_annotations": "count",
        "quality_score_trend": "percentage",
        "user_productivity": "tasks_per_hour"
    }
}
``` 