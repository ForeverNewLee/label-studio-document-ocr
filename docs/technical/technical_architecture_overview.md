# 敏感实体标注服务技术架构总览

## 1. 架构设计原则

### 1.1 核心原则
- **基于Label Studio**: 充分利用Label Studio现有能力，最小化定制开发
- **快速搭建**: 优先使用现成组件和插件，加速系统上线
- **可扩展**: 支持2万任务规模，具备水平扩展能力
- **安全可靠**: 保障敏感数据安全，支持数据脱敏需求

### 1.2 技术约束
- 必须基于现有Label Studio平台
- 保持与Label Studio生态兼容
- 优先使用Python/Django技术栈
- 支持标准的数据导入导出格式

## 2. 整体技术架构

### 2.1 系统架构图
```
┌─────────────────────────────────────────────────────────────┐
│                    负载均衡器 (Nginx)                        │
└─────────────────────┬───────────────────────────────────────┘
                     │
┌─────────────────────┴───────────────────────────────────────┐
│                  前端层 (React + LS Frontend)                │
└─────────────────────┬───────────────────────────────────────┘
                     │
┌─────────────────────┴───────────────────────────────────────┐
│              应用服务层 (Django + Label Studio)              │
├─────────────────────────────────────────────────────────────┤
│  标注模板配置  │  任务管理   │  质量控制   │  数据导出        │
│  Entity Config │  Task Mgmt  │  QC Module  │  Export API     │
└─────────────────────┬───────────────────────────────────────┘
                     │
┌─────────────────────┴───────────────────────────────────────┐
│                   数据存储层                                │
├─────────────────────┬───────────────────┬───────────────────┤
│  PostgreSQL         │  Redis Cache      │  File Storage     │
│  (主数据库)          │  (缓存/队列)       │  (OCR文件/导出)    │
└─────────────────────┴───────────────────┴───────────────────┘
```

### 2.2 核心组件

#### 2.2.1 Label Studio Core
- **版本**: Label Studio Community Edition (最新stable版本)
- **作用**: 提供标注界面、用户管理、项目管理核心功能
- **定制**: 通过配置和插件扩展，不修改核心代码

#### 2.2.2 自定义扩展组件
- **敏感实体标注模板**: 专门的NER标注配置
- **批量任务导入器**: 支持2万任务快速导入
- **质量控制模块**: 实时校验和审核流程
- **数据导出器**: 定制化的结果导出格式

## 3. 核心技术选型

### 3.1 基础技术栈

| 技术栈 | 选型 | 版本 | 说明 |
|-------|------|------|------|
| 标注平台 | Label Studio | 1.10+ | 开源数据标注平台 |
| 后端框架 | Django | 4.2+ | Label Studio原生技术栈 |
| 前端框架 | React | 18+ | Label Studio前端技术 |
| 数据库 | PostgreSQL | 14+ | 支持复杂查询和JSON |
| 缓存 | Redis | 7+ | 会话缓存和任务队列 |
| 任务队列 | Celery | 5+ | 异步任务处理 |
| Web服务器 | Nginx | 1.20+ | 反向代理和负载均衡 |
| 容器化 | Docker | 20+ | 应用打包和部署 |

### 3.2 Label Studio专用组件

#### 3.2.1 标注配置 (Labeling Config)
```xml
<View>
  <Header value="敏感实体标注任务"/>
  <Text name="text" value="$ocr_content"/>
  <View style="box-shadow: 2px 2px 5px #999; padding: 20px; margin-top: 2em;">
    <Header value="标注指令"/>
    <Text value="找出文档中没有被[MASK]框住的实体，将你找到的实体加入清单，并补全/检查清单中的实体类别。"/>
  </View>
  
  <Labels name="entity_type" toName="text">
    <!-- 人名相关 -->
    <Label value="FullName" background="red"/>
    <Label value="FirstName" background="darkred"/>  
    <Label value="LastName" background="lightcoral"/>
    
    <!-- 地址相关 -->
    <Label value="Address" background="blue"/>
    <Label value="StreetNumber" background="darkblue"/>
    <Label value="StreetName" background="lightblue"/>
    <Label value="City" background="navy"/>
    <Label value="State" background="skyblue"/>
    <Label value="ZipCode" background="steelblue"/>
    
    <!-- 证件号码 -->
    <Label value="InvoiceNumber" background="green"/>
    <Label value="CompanyName" background="darkgreen"/>
    <Label value="CheckNumber" background="lightgreen"/>
    
    <!-- 时间信息 -->
    <Label value="Date" background="orange"/>
    <Label value="MilitaryAddress" background="purple"/>
  </Labels>
</View>
```

#### 3.2.2 任务数据格式
```json
{
  "data": {
    "ocr_content": "From:\n[MASK_[MASK_Heather] [MASK_Hatfield]]\nINVOICE...",
    "document_name": "invoice_001.txt",
    "task_instruction": "找出文档中没有被[MASK]框住的实体..."
  },
  "meta": {
    "task_id": "task_001", 
    "priority": "normal",
    "estimated_time": 15
  }
}
```

## 4. 数据库设计

### 4.1 核心表结构

#### 4.1.1 扩展Label Studio原有表
```sql
-- 任务扩展信息表
CREATE TABLE ls_task_extension (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES task(id) ON DELETE CASCADE,
    document_name VARCHAR(255),
    ocr_content TEXT,
    task_instruction TEXT,
    entity_categories JSONB,
    priority VARCHAR(20) DEFAULT 'normal',
    estimated_time INTEGER DEFAULT 15,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 质量控制记录表  
CREATE TABLE quality_control_log (
    id SERIAL PRIMARY KEY,
    annotation_id INTEGER REFERENCES annotation(id) ON DELETE CASCADE,
    reviewer_id INTEGER REFERENCES auth_user(id),
    review_status VARCHAR(20), -- 'pending', 'approved', 'rejected'
    quality_score DECIMAL(3,2),
    feedback TEXT,
    review_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 标注统计表
CREATE TABLE annotation_statistics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id),
    date DATE DEFAULT CURRENT_DATE,
    tasks_completed INTEGER DEFAULT 0,
    entities_annotated INTEGER DEFAULT 0,
    avg_quality_score DECIMAL(3,2),
    total_time_spent INTEGER DEFAULT 0 -- 分钟
);
```

### 4.2 索引优化
```sql
-- 提升查询性能的索引
CREATE INDEX idx_task_extension_document ON ls_task_extension(document_name);
CREATE INDEX idx_task_extension_priority ON ls_task_extension(priority);
CREATE INDEX idx_quality_review_status ON quality_control_log(review_status);
CREATE INDEX idx_statistics_user_date ON annotation_statistics(user_id, date);
```

## 5. 系统集成设计

### 5.1 Label Studio定制化策略

#### 5.1.1 配置驱动定制
```python
# settings/label_studio_config.py
LABEL_STUDIO_SETTINGS = {
    'ENABLE_SIGNUP': False,  # 禁用自注册
    'DISABLE_SIGNUP_WITHOUT_LINK': True,
    'REQUIRE_EMAIL_CONFIRMATION': False,
    'ENABLE_LOCAL_FILES_STORAGE': True,
    'PROJECT_DEFAULTS': {
        'maximum_annotations': 1,
        'show_annotation_history': True,
        'show_ground_truth_first': False,
        'show_overlap_first': True,
        'overlap_cohort_percentage': 100,
        'task_data_login': None,
        'task_data_password': None,
        'control_weights': {},
        'model_version': '',
        'is_published': True,
        'show_instruction': True,
        'show_skip_button': True,
        'enable_empty_annotation': False,
        'show_submit_button': True,
        'show_hotkeys_help': True
    }
}
```

#### 5.1.2 自定义Django App集成
```python
# apps/sensitive_entity_annotation/apps.py
from django.apps import AppConfig

class SensitiveEntityAnnotationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sensitive_entity_annotation'
    verbose_name = '敏感实体标注'
    
    def ready(self):
        # 注册信号处理器
        import apps.sensitive_entity_annotation.signals
        # 注册自定义标注模板
        from .templates import register_templates
        register_templates()
```

### 5.2 API扩展设计

#### 5.2.1 批量任务导入API
```python
# apps/sensitive_entity_annotation/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from label_studio.projects.models import Project
from label_studio.tasks.models import Task

@api_view(['POST'])
def bulk_import_tasks(request):
    """批量导入标注任务"""
    project_id = request.data.get('project_id')
    tasks_data = request.data.get('tasks', [])
    
    project = Project.objects.get(id=project_id)
    created_tasks = []
    
    for task_data in tasks_data:
        # 创建任务
        task = Task.objects.create(
            project=project,
            data=task_data['data'],
            meta=task_data.get('meta', {})
        )
        
        # 创建扩展信息
        TaskExtension.objects.create(
            task=task,
            document_name=task_data['data']['document_name'],
            ocr_content=task_data['data']['ocr_content'],
            task_instruction=task_data['data']['task_instruction']
        )
        
        created_tasks.append(task.id)
    
    return Response({
        'created_tasks_count': len(created_tasks),
        'task_ids': created_tasks
    })
```

#### 5.2.2 质量控制API
```python
@api_view(['GET', 'POST'])
def quality_review(request, annotation_id):
    """质量审核接口"""
    annotation = Annotation.objects.get(id=annotation_id)
    
    if request.method == 'GET':
        # 获取审核信息
        review_log = QualityControlLog.objects.filter(
            annotation=annotation
        ).first()
        return Response(QualityControlLogSerializer(review_log).data)
    
    elif request.method == 'POST':
        # 提交审核结果
        review_data = request.data
        QualityControlLog.objects.create(
            annotation=annotation,
            reviewer=request.user,
            review_status=review_data['status'],
            quality_score=review_data['score'],
            feedback=review_data.get('feedback', '')
        )
        return Response({'status': 'success'})
```

### 5.3 前端定制

#### 5.3.1 React组件扩展
```javascript
// frontend/src/components/SensitiveEntityPanel.jsx
import React from 'react';
import { observer } from 'mobx-react';

const SensitiveEntityPanel = observer(({ annotation }) => {
  const entityCategories = {
    '人名相关': ['FullName', 'FirstName', 'LastName'],
    '地址相关': ['Address', 'StreetNumber', 'StreetName', 'City', 'State', 'ZipCode'],
    '证件号码': ['InvoiceNumber', 'CompanyName', 'CheckNumber'],
    '时间信息': ['Date', 'MilitaryAddress']
  };

  return (
    <div className="sensitive-entity-panel">
      <h3>实体分类</h3>
      {Object.entries(entityCategories).map(([category, labels]) => (
        <div key={category} className="category-group">
          <h4>{category}</h4>
          {labels.map(label => (
            <div key={label} className="label-item">
              <span className="label-name">{label}</span>
              <button onClick={() => selectLabel(label)}>选择</button>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
});

export default SensitiveEntityPanel;
```

## 6. 部署架构

### 6.1 容器化部署

#### 6.1.1 Docker Compose配置
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DJANGO_DB=postgresql://user:pass@db:5432/labelstudio
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/label-studio/data
      - ./media:/label-studio/media

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: labelstudio
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app

  celery:
    build: .
    command: celery -A label_studio.core worker -l info
    environment:
      - DJANGO_DB=postgresql://user:pass@db:5432/labelstudio
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  redis_data:
```

#### 6.1.2 应用Dockerfile
```dockerfile
# Dockerfile
FROM heartexlabs/label-studio:latest

# 安装自定义依赖
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# 复制自定义应用
COPY apps/ /label-studio/apps/
COPY settings/ /label-studio/settings/

# 复制静态文件和模板
COPY templates/ /label-studio/templates/
COPY static/ /label-studio/static/

# 设置环境变量
ENV LABEL_STUDIO_BASE_DATA_DIR=/label-studio/data
ENV LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
ENV LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=/label-studio/data

# 运行迁移和收集静态文件
RUN python manage.py migrate
RUN python manage.py collectstatic --noinput

EXPOSE 8080
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
```

### 6.2 扩展性考虑

#### 6.2.1 水平扩展
- **应用层**: 通过负载均衡器支持多实例部署
- **数据库**: PostgreSQL主从复制，读写分离
- **缓存**: Redis集群模式
- **文件存储**: 共享存储或对象存储

#### 6.2.2 性能优化
```python
# settings/performance.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'labelstudio',
        'OPTIONS': {
            'MAX_CONNS': 100,
            'conn_max_age': 0,
        }
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50}
        }
    }
}

# Celery配置
CELERY_BROKER_URL = 'redis://redis:6379/2'
CELERY_RESULT_BACKEND = 'redis://redis:6379/2'
CELERY_WORKER_CONCURRENCY = 4
CELERY_TASK_SOFT_TIME_LIMIT = 300
```

## 7. 安全设计

### 7.1 数据安全

#### 7.1.1 敏感数据处理
```python
# apps/security/middleware.py
class SensitiveDataMiddleware:
    """敏感数据处理中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 请求前处理
        if hasattr(request, 'user') and request.user.is_authenticated:
            # 记录用户操作日志
            self.log_user_action(request)
        
        response = self.get_response(request)
        
        # 响应后处理
        if 'ocr_content' in str(response.content):
            # 标记敏感数据响应
            response['X-Contains-Sensitive-Data'] = 'true'
        
        return response
    
    def log_user_action(self, request):
        """记录用户操作"""
        UserActionLog.objects.create(
            user=request.user,
            action=f"{request.method} {request.path}",
            ip_address=self.get_client_ip(request),
            timestamp=timezone.now()
        )
```

#### 7.1.2 数据加密
```python
# apps/security/encryption.py
from cryptography.fernet import Fernet
from django.conf import settings

class DataEncryption:
    """数据加密工具"""
    
    def __init__(self):
        self.cipher_suite = Fernet(settings.ENCRYPTION_KEY)
    
    def encrypt_ocr_content(self, content):
        """加密OCR内容"""
        if not content:
            return content
        return self.cipher_suite.encrypt(content.encode()).decode()
    
    def decrypt_ocr_content(self, encrypted_content):
        """解密OCR内容"""
        if not encrypted_content:
            return encrypted_content
        return self.cipher_suite.decrypt(encrypted_content.encode()).decode()
```

### 7.2 访问控制

#### 7.2.1 角色权限设计
```python
# apps/security/permissions.py
from rest_framework.permissions import BasePermission

class AnnotatorPermission(BasePermission):
    """标注员权限"""
    def has_permission(self, request, view):
        return request.user.has_perm('annotation.can_annotate')

class ReviewerPermission(BasePermission):
    """审核员权限"""
    def has_permission(self, request, view):
        return request.user.has_perm('annotation.can_review')

class ProjectManagerPermission(BasePermission):
    """项目管理员权限"""
    def has_permission(self, request, view):
        return request.user.has_perm('project.can_manage')
```

## 8. 监控和日志

### 8.1 系统监控

#### 8.1.1 健康检查
```python
# apps/monitoring/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """系统健康检查"""
    try:
        # 检查数据库连接
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # 检查Redis连接
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'components': {
                'database': 'ok',
                'cache': 'ok'
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)
```

#### 8.1.2 性能指标
```python
# apps/monitoring/metrics.py
import time
from functools import wraps

def track_performance(func):
    """性能跟踪装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # 记录性能指标
        PerformanceMetric.objects.create(
            function_name=func.__name__,
            execution_time=execution_time,
            timestamp=timezone.now()
        )
        
        return result
    return wrapper
```

## 9. 开发和部署流程

### 9.1 开发环境设置

#### 9.1.1 本地开发
```bash
# 环境安装脚本
#!/bin/bash
# setup_dev.sh

# 安装Label Studio
pip install label-studio

# 安装自定义依赖
pip install -r requirements.txt

# 设置环境变量
export LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
export LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=./data

# 初始化数据库
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

### 9.2 部署流程

#### 9.2.1 生产部署
```bash
# 部署脚本
#!/bin/bash
# deploy.sh

# 构建Docker镜像
docker-compose build

# 运行数据库迁移
docker-compose run --rm app python manage.py migrate

# 收集静态文件
docker-compose run --rm app python manage.py collectstatic --noinput

# 启动服务
docker-compose up -d

# 健康检查
curl -f http://localhost/health/ || exit 1

echo "部署完成"
```

## 10. 总结

这个技术架构设计完全基于Label Studio构建，通过配置、扩展和插件的方式实现敏感实体标注的专业化需求。主要特点：

### 10.1 架构优势
- **快速部署**: 基于成熟的Label Studio，减少开发周期
- **成本可控**: 最大化复用现有功能，最小化定制开发
- **易于维护**: 保持与Label Studio生态的兼容性
- **扩展性强**: 支持大规模数据处理和并发访问

### 10.2 技术亮点
- **专业化配置**: 针对敏感实体识别的标注模板
- **批量处理**: 支持2万任务的高效导入和管理
- **质量保证**: 完整的质量控制和审核机制
- **安全设计**: 敏感数据的加密和访问控制

这个架构能够快速满足敏感实体标注的业务需求，同时保持良好的可维护性和扩展性。