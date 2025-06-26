# 数据库设计文档

## 1. 设计原则

### 1.1 核心原则
- **非侵入式扩展**: 不修改Label Studio原有表结构
- **关联性设计**: 通过外键关联扩展原有功能
- **性能优化**: 合理设计索引提升查询性能
- **数据完整性**: 确保数据一致性和完整性约束

### 1.2 设计策略
```
Label Studio原有表 (保持不变)
├── auth_user (用户表)
├── project (项目表)
├── task (任务表)
├── annotation (标注表)
└── organization (组织表)

扩展表 (新增)
├── ls_task_extension (任务扩展表)
├── quality_control_log (质量控制表)
├── annotation_statistics (标注统计表)
├── entity_classification (实体分类表)
└── system_config (系统配置表)
```

## 2. 核心表设计

### 2.1 任务扩展表 (ls_task_extension)
```sql
CREATE TABLE ls_task_extension (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES task(id) ON DELETE CASCADE,
    document_name VARCHAR(255) NOT NULL,
    ocr_content TEXT NOT NULL,
    task_instruction TEXT,
    entity_categories JSONB DEFAULT '{}',
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    estimated_time INTEGER DEFAULT 15 CHECK (estimated_time > 0),
    actual_time INTEGER DEFAULT 0 CHECK (actual_time >= 0),
    difficulty_level VARCHAR(20) DEFAULT 'medium' CHECK (difficulty_level IN ('easy', 'medium', 'hard')),
    document_type VARCHAR(50) DEFAULT 'unknown',
    source_batch VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT unique_task_extension UNIQUE (task_id),
    CONSTRAINT valid_document_name CHECK (LENGTH(document_name) > 0),
    CONSTRAINT valid_ocr_content CHECK (LENGTH(ocr_content) > 0)
);

-- 索引
CREATE INDEX idx_task_ext_document_name ON ls_task_extension(document_name);
CREATE INDEX idx_task_ext_priority ON ls_task_extension(priority);
CREATE INDEX idx_task_ext_batch ON ls_task_extension(source_batch);
CREATE INDEX idx_task_ext_type ON ls_task_extension(document_type);
CREATE INDEX idx_task_ext_created ON ls_task_extension(created_at);

-- 触发器：自动更新updated_at
CREATE OR REPLACE FUNCTION update_task_extension_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_task_extension_timestamp
    BEFORE UPDATE ON ls_task_extension
    FOR EACH ROW
    EXECUTE FUNCTION update_task_extension_timestamp();
```

### 2.2 质量控制表 (quality_control_log)
```sql
CREATE TABLE quality_control_log (
    id SERIAL PRIMARY KEY,
    annotation_id INTEGER REFERENCES annotation(id) ON DELETE CASCADE,
    reviewer_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    review_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    quality_score DECIMAL(3,2) CHECK (quality_score >= 0 AND quality_score <= 1),
    completeness_score DECIMAL(3,2) CHECK (completeness_score >= 0 AND completeness_score <= 1),
    accuracy_score DECIMAL(3,2) CHECK (accuracy_score >= 0 AND accuracy_score <= 1),
    consistency_score DECIMAL(3,2) CHECK (consistency_score >= 0 AND consistency_score <= 1),
    feedback TEXT,
    feedback_category VARCHAR(50),
    auto_check_results JSONB DEFAULT '{}',
    manual_check_results JSONB DEFAULT '{}',
    review_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT check_review_status CHECK (
        review_status IN ('pending', 'in_review', 'approved', 'rejected', 'needs_revision')
    ),
    CONSTRAINT check_feedback_category CHECK (
        feedback_category IN ('missing_entities', 'wrong_classification', 'formatting_error', 'inconsistency', 'other')
    )
);

-- 索引
CREATE INDEX idx_qc_annotation ON quality_control_log(annotation_id);
CREATE INDEX idx_qc_reviewer ON quality_control_log(reviewer_id);
CREATE INDEX idx_qc_status ON quality_control_log(review_status);
CREATE INDEX idx_qc_review_time ON quality_control_log(review_time);
CREATE INDEX idx_qc_quality_score ON quality_control_log(quality_score);
```

### 2.3 标注统计表 (annotation_statistics)
```sql
CREATE TABLE annotation_statistics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES project(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    tasks_completed INTEGER DEFAULT 0 CHECK (tasks_completed >= 0),
    tasks_approved INTEGER DEFAULT 0 CHECK (tasks_approved >= 0),
    tasks_rejected INTEGER DEFAULT 0 CHECK (tasks_rejected >= 0),
    entities_annotated INTEGER DEFAULT 0 CHECK (entities_annotated >= 0),
    avg_quality_score DECIMAL(3,2) CHECK (avg_quality_score >= 0 AND avg_quality_score <= 1),
    avg_completeness_score DECIMAL(3,2) CHECK (avg_completeness_score >= 0 AND avg_completeness_score <= 1),
    total_time_spent INTEGER DEFAULT 0 CHECK (total_time_spent >= 0), -- 秒
    avg_time_per_task INTEGER DEFAULT 0 CHECK (avg_time_per_task >= 0), -- 秒
    productivity_score DECIMAL(3,2) CHECK (productivity_score >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT unique_user_project_date UNIQUE (user_id, project_id, date),
    CONSTRAINT check_approved_rejected CHECK (tasks_approved + tasks_rejected <= tasks_completed)
);

-- 索引
CREATE INDEX idx_stats_user_date ON annotation_statistics(user_id, date);
CREATE INDEX idx_stats_project_date ON annotation_statistics(project_id, date);
CREATE INDEX idx_stats_date ON annotation_statistics(date);
CREATE INDEX idx_stats_quality ON annotation_statistics(avg_quality_score);
```

### 2.4 实体分类配置表 (entity_classification)
```sql
CREATE TABLE entity_classification (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    label_code VARCHAR(50) NOT NULL,
    label_display VARCHAR(100) NOT NULL,
    description TEXT,
    color_code VARCHAR(7) DEFAULT '#666666',
    hotkey VARCHAR(1),
    parent_category_id INTEGER REFERENCES entity_classification(id) ON DELETE SET NULL,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    example_texts JSONB DEFAULT '[]',
    validation_rules JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT unique_label_code UNIQUE (label_code),
    CONSTRAINT unique_hotkey UNIQUE (hotkey),
    CONSTRAINT check_color_format CHECK (color_code ~ '^#[0-9A-Fa-f]{6}$'),
    CONSTRAINT check_hotkey_format CHECK (hotkey ~ '^[0-9a-zA-Z]$')
);

-- 初始化数据
INSERT INTO entity_classification (category_name, label_code, label_display, description, color_code, hotkey, sort_order) VALUES
-- 人名相关
('人名相关', 'FullName', '完整姓名', '完整的人名，包含姓和名', '#dc3545', '1', 1),
('人名相关', 'FirstName', '名', '人名的名字部分', '#c82333', '2', 2),
('人名相关', 'LastName', '姓', '人名的姓氏部分', '#e85563', '3', 3),

-- 地址相关
('地址相关', 'Address', '完整地址', '完整的地址信息', '#007bff', '4', 4),
('地址相关', 'StreetNumber', '街道号', '街道门牌号码', '#0056b3', '5', 5),
('地址相关', 'StreetName', '街道名', '街道名称', '#3395ff', '6', 6),
('地址相关', 'City', '城市', '城市名称', '#004085', '7', 7),
('地址相关', 'State', '州/省', '州或省份名称', '#66b5ff', '8', 8),
('地址相关', 'ZipCode', '邮编', '邮政编码', '#1a88ff', '9', 9),

-- 证件号码
('证件号码', 'InvoiceNumber', '发票号', '发票或单据编号', '#28a745', 'q', 10),
('证件号码', 'CompanyName', '公司名称', '公司或组织名称', '#1e7e34', 'w', 11),
('证件号码', 'CheckNumber', '支票号', '支票编号', '#5cb85c', 'e', 12),

-- 时间信息
('时间信息', 'Date', '日期', '日期时间信息', '#fd7e14', 'r', 13),
('时间信息', 'MilitaryAddress', '军事地址', '军事邮政地址', '#6f42c1', 't', 14);

-- 索引
CREATE INDEX idx_entity_category ON entity_classification(category_name);
CREATE INDEX idx_entity_active ON entity_classification(is_active);
CREATE INDEX idx_entity_sort ON entity_classification(sort_order);
```

### 2.5 系统配置表 (system_config)
```sql
CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    config_type VARCHAR(20) DEFAULT 'string' CHECK (
        config_type IN ('string', 'integer', 'boolean', 'json', 'float')
    ),
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    is_editable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 初始化系统配置
INSERT INTO system_config (config_key, config_value, config_type, description, is_system) VALUES
('max_batch_import_size', '1000', 'integer', '最大批量导入任务数', TRUE),
('default_task_priority', 'normal', 'string', '默认任务优先级', TRUE),
('quality_threshold', '0.95', 'float', '质量阈值', TRUE),
('enable_auto_validation', 'true', 'boolean', '启用自动验证', TRUE),
('annotation_timeout_minutes', '30', 'integer', '标注超时时间(分钟)', TRUE),
('export_formats', '["json", "csv", "xlsx"]', 'json', '支持的导出格式', TRUE);

-- 索引
CREATE INDEX idx_config_key ON system_config(config_key);
CREATE INDEX idx_config_type ON system_config(config_type);
```

## 3. 视图和查询优化

### 3.1 统计视图
```sql
-- 项目进度统计视图
CREATE VIEW project_progress_stats AS
SELECT 
    p.id as project_id,
    p.title as project_title,
    COUNT(t.id) as total_tasks,
    COUNT(a.id) as completed_tasks,
    COUNT(CASE WHEN qc.review_status = 'approved' THEN 1 END) as approved_tasks,
    COUNT(CASE WHEN qc.review_status = 'rejected' THEN 1 END) as rejected_tasks,
    ROUND(
        COUNT(a.id)::DECIMAL / NULLIF(COUNT(t.id), 0) * 100, 2
    ) as completion_percentage,
    ROUND(
        AVG(qc.quality_score), 3
    ) as avg_quality_score
FROM project p
LEFT JOIN task t ON p.id = t.project_id
LEFT JOIN annotation a ON t.id = a.task_id AND a.was_cancelled = FALSE
LEFT JOIN quality_control_log qc ON a.id = qc.annotation_id
GROUP BY p.id, p.title;

-- 用户绩效统计视图
CREATE VIEW user_performance_stats AS
SELECT 
    u.id as user_id,
    u.username,
    u.first_name,
    u.last_name,
    COUNT(a.id) as total_annotations,
    COUNT(CASE WHEN qc.review_status = 'approved' THEN 1 END) as approved_annotations,
    ROUND(
        COUNT(CASE WHEN qc.review_status = 'approved' THEN 1 END)::DECIMAL / 
        NULLIF(COUNT(qc.id), 0) * 100, 2
    ) as approval_rate,
    ROUND(AVG(qc.quality_score), 3) as avg_quality_score,
    SUM(ext.actual_time) as total_time_minutes
FROM auth_user u
LEFT JOIN annotation a ON u.id = a.completed_by_id AND a.was_cancelled = FALSE
LEFT JOIN quality_control_log qc ON a.id = qc.annotation_id
LEFT JOIN task t ON a.task_id = t.id
LEFT JOIN ls_task_extension ext ON t.id = ext.task_id
GROUP BY u.id, u.username, u.first_name, u.last_name;

-- 实体类型分布视图
CREATE VIEW entity_type_distribution AS
SELECT 
    ec.category_name,
    ec.label_code,
    ec.label_display,
    COUNT(*) as usage_count,
    ROUND(
        COUNT(*)::DECIMAL / SUM(COUNT(*)) OVER() * 100, 2
    ) as usage_percentage
FROM entity_classification ec
JOIN annotation a ON a.result::text LIKE '%' || ec.label_code || '%'
WHERE ec.is_active = TRUE
GROUP BY ec.category_name, ec.label_code, ec.label_display
ORDER BY usage_count DESC;
```

### 3.2 存储过程
```sql
-- 批量更新任务优先级
CREATE OR REPLACE FUNCTION update_task_priority(
    p_project_id INTEGER,
    p_old_priority VARCHAR,
    p_new_priority VARCHAR
) RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE ls_task_extension 
    SET priority = p_new_priority,
        updated_at = CURRENT_TIMESTAMP
    WHERE task_id IN (
        SELECT id FROM task WHERE project_id = p_project_id
    ) AND priority = p_old_priority;
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- 计算用户日统计
CREATE OR REPLACE FUNCTION calculate_daily_stats(
    p_user_id INTEGER,
    p_project_id INTEGER,
    p_date DATE DEFAULT CURRENT_DATE
) RETURNS VOID AS $$
DECLARE
    stats_record RECORD;
BEGIN
    -- 计算当日统计数据
    SELECT 
        COUNT(DISTINCT a.task_id) as tasks_completed,
        COUNT(CASE WHEN qc.review_status = 'approved' THEN 1 END) as tasks_approved,
        COUNT(CASE WHEN qc.review_status = 'rejected' THEN 1 END) as tasks_rejected,
        COUNT(*) as entities_annotated,
        AVG(qc.quality_score) as avg_quality_score,
        AVG(qc.completeness_score) as avg_completeness_score,
        SUM(ext.actual_time) * 60 as total_time_spent -- 转换为秒
    INTO stats_record
    FROM annotation a
    JOIN task t ON a.task_id = t.id
    JOIN ls_task_extension ext ON t.id = ext.task_id
    LEFT JOIN quality_control_log qc ON a.id = qc.annotation_id
    WHERE a.completed_by_id = p_user_id 
      AND t.project_id = p_project_id
      AND DATE(a.created_at) = p_date
      AND a.was_cancelled = FALSE;

    -- 插入或更新统计记录
    INSERT INTO annotation_statistics (
        user_id, project_id, date,
        tasks_completed, tasks_approved, tasks_rejected,
        entities_annotated, avg_quality_score, avg_completeness_score,
        total_time_spent,
        avg_time_per_task
    ) VALUES (
        p_user_id, p_project_id, p_date,
        COALESCE(stats_record.tasks_completed, 0),
        COALESCE(stats_record.tasks_approved, 0),
        COALESCE(stats_record.tasks_rejected, 0),
        COALESCE(stats_record.entities_annotated, 0),
        stats_record.avg_quality_score,
        stats_record.avg_completeness_score,
        COALESCE(stats_record.total_time_spent, 0),
        CASE 
            WHEN COALESCE(stats_record.tasks_completed, 0) > 0 
            THEN COALESCE(stats_record.total_time_spent, 0) / stats_record.tasks_completed
            ELSE 0
        END
    )
    ON CONFLICT (user_id, project_id, date) 
    DO UPDATE SET
        tasks_completed = EXCLUDED.tasks_completed,
        tasks_approved = EXCLUDED.tasks_approved,
        tasks_rejected = EXCLUDED.tasks_rejected,
        entities_annotated = EXCLUDED.entities_annotated,
        avg_quality_score = EXCLUDED.avg_quality_score,
        avg_completeness_score = EXCLUDED.avg_completeness_score,
        total_time_spent = EXCLUDED.total_time_spent,
        avg_time_per_task = EXCLUDED.avg_time_per_task,
        updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;
```

## 4. 性能优化

### 4.1 索引策略
```sql
-- 复合索引
CREATE INDEX idx_task_project_created ON task(project_id, created_at);
CREATE INDEX idx_annotation_task_user ON annotation(task_id, completed_by_id) WHERE was_cancelled = FALSE;
CREATE INDEX idx_qc_status_time ON quality_control_log(review_status, review_time);

-- 部分索引
CREATE INDEX idx_active_tasks ON task(id) WHERE is_labeled = FALSE;
CREATE INDEX idx_pending_reviews ON quality_control_log(annotation_id) WHERE review_status = 'pending';

-- GIN索引（用于JSONB字段）
CREATE INDEX idx_entity_categories_gin ON ls_task_extension USING GIN (entity_categories);
CREATE INDEX idx_auto_check_results_gin ON quality_control_log USING GIN (auto_check_results);
```

### 4.2 查询优化示例
```sql
-- 优化前：查询用户待标注任务
SELECT t.id, t.data, ext.document_name, ext.priority
FROM task t
JOIN ls_task_extension ext ON t.id = ext.task_id
WHERE t.project_id = $1 
  AND t.is_labeled = FALSE
  AND NOT EXISTS (
      SELECT 1 FROM annotation a 
      WHERE a.task_id = t.id AND a.completed_by_id = $2
  );

-- 优化后：使用LEFT JOIN和IS NULL
SELECT t.id, t.data, ext.document_name, ext.priority
FROM task t
JOIN ls_task_extension ext ON t.id = ext.task_id
LEFT JOIN annotation a ON t.id = a.task_id AND a.completed_by_id = $2
WHERE t.project_id = $1 
  AND t.is_labeled = FALSE
  AND a.id IS NULL
ORDER BY 
  CASE ext.priority 
    WHEN 'urgent' THEN 1
    WHEN 'high' THEN 2
    WHEN 'normal' THEN 3
    WHEN 'low' THEN 4
  END,
  t.created_at;
```

## 5. 数据迁移脚本

### 5.1 初始化脚本
```sql
-- 数据库初始化脚本
-- 创建所有扩展表和索引

BEGIN;

-- 创建扩展表
\i create_extension_tables.sql

-- 创建索引
\i create_indexes.sql

-- 创建视图
\i create_views.sql

-- 创建存储过程
\i create_procedures.sql

-- 初始化配置数据
\i insert_initial_data.sql

COMMIT;
```

### 5.2 数据清理脚本
```sql
-- 清理过期数据
CREATE OR REPLACE FUNCTION cleanup_old_data() RETURNS VOID AS $$
BEGIN
    -- 清理30天前的质量控制日志
    DELETE FROM quality_control_log 
    WHERE review_time < NOW() - INTERVAL '30 days';
    
    -- 清理90天前的统计数据
    DELETE FROM annotation_statistics 
    WHERE date < CURRENT_DATE - INTERVAL '90 days';
    
    -- 清理无效的任务扩展记录
    DELETE FROM ls_task_extension 
    WHERE task_id NOT IN (SELECT id FROM task);
    
    -- 记录清理日志
    INSERT INTO system_config (config_key, config_value, description)
    VALUES (
        'last_cleanup_time', 
        NOW()::TEXT, 
        '最后数据清理时间'
    )
    ON CONFLICT (config_key) 
    DO UPDATE SET 
        config_value = EXCLUDED.config_value,
        updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- 创建定时清理任务（需要pg_cron扩展）
-- SELECT cron.schedule('cleanup-old-data', '0 2 * * 0', 'SELECT cleanup_old_data();');
```

## 6. 监控和维护

### 6.1 监控查询
```sql
-- 数据库性能监控
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public' 
  AND tablename IN ('ls_task_extension', 'quality_control_log', 'annotation_statistics');

-- 表大小监控
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;

-- 索引使用情况
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

### 6.2 备份策略
```bash
#!/bin/bash
# backup_database.sh

# 数据库连接信息
DB_HOST="localhost"
DB_NAME="labelstudio"
DB_USER="postgres"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 全量备份
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
    --format=custom \
    --file="$BACKUP_DIR/labelstudio_full_$DATE.dump"

# 仅备份扩展表
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
    --format=custom \
    --table="ls_task_extension" \
    --table="quality_control_log" \
    --table="annotation_statistics" \
    --table="entity_classification" \
    --table="system_config" \
    --file="$BACKUP_DIR/labelstudio_extensions_$DATE.dump"

# 清理7天前的备份
find $BACKUP_DIR -name "*.dump" -mtime +7 -delete
```

这个数据库设计确保了系统的高性能、可维护性和数据完整性，同时为敏感实体标注服务提供了完整的数据支撑。