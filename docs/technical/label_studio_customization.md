# Label Studio定制化方案

## 1. 定制化策略

### 1.1 核心原则
- **配置优先**: 通过配置文件实现功能定制，避免修改核心代码
- **插件扩展**: 使用Django app模式扩展功能
- **模板定制**: 通过自定义标注模板实现专业化界面
- **API扩展**: 通过REST API扩展实现批量操作

### 1.2 定制范围
```
Label Studio Core (不修改)
├── 用户管理 ✓
├── 项目管理 ✓  
├── 任务管理 ✓
└── 基础标注界面 ✓

自定义扩展 (新增)
├── 敏感实体标注模板
├── 批量任务导入
├── 质量控制模块
└── 专业化导出
```

## 2. 标注模板配置

### 2.1 敏感实体NER模板
```xml
<View>
  <!-- 标注指令区域 -->
  <View style="box-shadow: 2px 2px 5px #999; padding: 20px; margin-bottom: 2em; background: #f8f9fa;">
    <Header value="📋 敏感实体标注任务"/>
    <Text value="请识别文档中的所有敏感实体并进行分类标注，包括被[MASK]遮挡的和未遮挡的敏感信息。"/>
    
    <View style="margin-top: 10px; padding: 10px; background: #e9ecef; border-radius: 5px;">
      <Text value="🎯 标注要求：1) 扫描MASK内容 2) 识别未遮挡敏感信息 3) 复合实体分解"/>
    </View>
  </View>

  <!-- 文档内容展示 -->
  <Text name="text" value="$ocr_content" 
        style="padding: 20px; border: 1px solid #ddd; border-radius: 5px; background: white; font-family: monospace; line-height: 1.6;"/>

  <!-- 实体分类标签 -->
  <Labels name="entity_type" toName="text" choice="multiple">
    <!-- 人名相关 -->
    <Label value="FullName" background="#dc3545" hotkey="1"/>
    <Label value="FirstName" background="#c82333" hotkey="2"/>  
    <Label value="LastName" background="#e85563" hotkey="3"/>
    
    <!-- 地址相关 -->
    <Label value="Address" background="#007bff" hotkey="4"/>
    <Label value="StreetNumber" background="#0056b3" hotkey="5"/>
    <Label value="StreetName" background="#3395ff" hotkey="6"/>
    <Label value="City" background="#004085" hotkey="7"/>
    <Label value="State" background="#66b5ff" hotkey="8"/>
    <Label value="ZipCode" background="#1a88ff" hotkey="9"/>
    
    <!-- 证件号码 -->
    <Label value="InvoiceNumber" background="#28a745" hotkey="q"/>
    <Label value="CompanyName" background="#1e7e34" hotkey="w"/>
    <Label value="CheckNumber" background="#5cb85c" hotkey="e"/>
    
    <!-- 时间信息 -->
    <Label value="Date" background="#fd7e14" hotkey="r"/>
    <Label value="MilitaryAddress" background="#6f42c1" hotkey="t"/>
  </Labels>

  <!-- 标注结果预览 -->
  <View style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px;">
    <Header value="✅ 标注结果预览"/>
    <Text value="已标注实体将在此处实时显示"/>
  </View>
</View>
```

### 2.2 标注配置参数
```python
# apps/sensitive_entity_annotation/templates.py
SENSITIVE_ENTITY_TEMPLATE = {
    "title": "敏感实体标注模板",
    "description": "专用于英文票据OCR文档的敏感实体识别和分类标注",
    "label_config": LABEL_CONFIG_XML,
    "expert_instruction": """
标注专家指导：
1. 仔细扫描所有[MASK]标记，识别被遮挡的敏感信息类型
2. 检查未被遮挡的文本，识别潜在的敏感实体
3. 对复合实体进行分解标注（如：完整姓名 → 姓 + 名）
4. 确保标注的一致性和完整性
5. 特别关注：军事地址、公司名称、发票号等特殊实体
""",
    "data_fields": {
        "ocr_content": "OCR处理后的文档内容",
        "document_name": "文档名称",
        "task_instruction": "任务指令"
    }
}
```

## 3. 自定义Django应用

### 3.1 应用结构
```
apps/sensitive_entity_annotation/
├── __init__.py
├── apps.py
├── models.py          # 扩展数据模型
├── views.py           # 自定义API接口
├── serializers.py     # 数据序列化器
├── templates.py       # 标注模板定义
├── signals.py         # 信号处理器
├── management/        # 管理命令
│   └── commands/
│       ├── import_tasks.py
│       └── export_annotations.py
└── migrations/        # 数据库迁移
```

### 3.2 扩展模型定义
```python
# apps/sensitive_entity_annotation/models.py
from django.db import models
from label_studio.tasks.models import Task, Annotation
from django.contrib.auth.models import User

class TaskExtension(models.Model):
    """任务扩展信息"""
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    document_name = models.CharField(max_length=255)
    ocr_content = models.TextField()
    task_instruction = models.TextField()
    entity_categories = models.JSONField(default=dict)
    priority = models.CharField(max_length=20, default='normal')
    estimated_time = models.IntegerField(default=15)  # 分钟
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ls_task_extension'

class QualityControlLog(models.Model):
    """质量控制记录"""
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('approved', '通过'),
        ('rejected', '退回'),
    ]
    
    annotation = models.ForeignKey(Annotation, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    review_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    quality_score = models.DecimalField(max_digits=3, decimal_places=2, null=True)
    feedback = models.TextField(blank=True)
    review_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'quality_control_log'

class AnnotationStatistics(models.Model):
    """标注统计"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    tasks_completed = models.IntegerField(default=0)
    entities_annotated = models.IntegerField(default=0)
    avg_quality_score = models.DecimalField(max_digits=3, decimal_places=2, null=True)
    total_time_spent = models.IntegerField(default=0)  # 分钟

    class Meta:
        db_table = 'annotation_statistics'
        unique_together = ['user', 'date']
```

### 3.3 批量导入接口
```python
# apps/sensitive_entity_annotation/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from label_studio.projects.models import Project
from label_studio.tasks.models import Task
from .models import TaskExtension
import json

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_import_tasks(request):
    """批量导入标注任务"""
    try:
        project_id = request.data.get('project_id')
        tasks_data = request.data.get('tasks', [])
        
        if not project_id or not tasks_data:
            return Response(
                {'error': '缺少必要参数'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        project = Project.objects.get(id=project_id)
        created_tasks = []
        
        for task_data in tasks_data:
            # 创建基础任务
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
                task_instruction=task_data['data'].get('task_instruction', ''),
                priority=task_data.get('meta', {}).get('priority', 'normal'),
                estimated_time=task_data.get('meta', {}).get('estimated_time', 15)
            )
            
            created_tasks.append({
                'task_id': task.id,
                'document_name': task_data['data']['document_name']
            })
        
        return Response({
            'success': True,
            'created_tasks_count': len(created_tasks),
            'tasks': created_tasks
        })
        
    except Project.DoesNotExist:
        return Response(
            {'error': '项目不存在'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_annotations(request, project_id):
    """导出标注结果"""
    try:
        project = Project.objects.get(id=project_id)
        tasks = Task.objects.filter(project=project).prefetch_related('annotations')
        
        export_data = []
        for task in tasks:
            task_extension = getattr(task, 'taskextension', None)
            
            for annotation in task.annotations.all():
                annotation_data = {
                    'task_id': task.id,
                    'document_name': task_extension.document_name if task_extension else '',
                    'ocr_content': task.data.get('ocr_content', ''),
                    'annotation_result': annotation.result,
                    'created_at': annotation.created_at.isoformat(),
                    'annotator': annotation.completed_by.username if annotation.completed_by else None
                }
                export_data.append(annotation_data)
        
        return Response({
            'project_id': project_id,
            'project_title': project.title,
            'export_time': timezone.now().isoformat(),
            'annotations_count': len(export_data),
            'annotations': export_data
        })
        
    except Project.DoesNotExist:
        return Response(
            {'error': '项目不存在'}, 
            status=status.HTTP_404_NOT_FOUND
        )
```

## 4. 管理命令

### 4.1 批量导入命令
```python
# apps/sensitive_entity_annotation/management/commands/import_tasks.py
from django.core.management.base import BaseCommand
from django.db import transaction
from label_studio.projects.models import Project
from label_studio.tasks.models import Task
from apps.sensitive_entity_annotation.models import TaskExtension
import json
import os

class Command(BaseCommand):
    help = '批量导入敏感实体标注任务'

    def add_arguments(self, parser):
        parser.add_argument('--project-id', type=int, required=True, help='项目ID')
        parser.add_argument('--data-file', type=str, required=True, help='数据文件路径')
        parser.add_argument('--batch-size', type=int, default=100, help='批次大小')

    def handle(self, *args, **options):
        project_id = options['project_id']
        data_file = options['data_file']
        batch_size = options['batch_size']
        
        try:
            project = Project.objects.get(id=project_id)
            self.stdout.write(f"开始导入项目: {project.title}")
            
            with open(data_file, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
            
            total_tasks = len(tasks_data)
            created_count = 0
            
            # 分批处理
            for i in range(0, total_tasks, batch_size):
                batch_data = tasks_data[i:i + batch_size]
                
                with transaction.atomic():
                    for task_data in batch_data:
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
                            task_instruction=task_data['data'].get('task_instruction', ''),
                            priority=task_data.get('meta', {}).get('priority', 'normal')
                        )
                        
                        created_count += 1
                
                self.stdout.write(f"已导入 {created_count}/{total_tasks} 个任务")
            
            self.stdout.write(
                self.style.SUCCESS(f'成功导入 {created_count} 个标注任务')
            )
            
        except Project.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'项目 {project_id} 不存在')
            )
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'数据文件 {data_file} 不存在')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'导入失败: {str(e)}')
            )
```

### 4.2 导出命令
```python
# apps/sensitive_entity_annotation/management/commands/export_annotations.py
from django.core.management.base import BaseCommand
from label_studio.projects.models import Project
from label_studio.tasks.models import Task
import json
import os
from datetime import datetime

class Command(BaseCommand):
    help = '导出敏感实体标注结果'

    def add_arguments(self, parser):
        parser.add_argument('--project-id', type=int, required=True)
        parser.add_argument('--output-file', type=str, required=True)
        parser.add_argument('--format', choices=['json', 'csv'], default='json')

    def handle(self, *args, **options):
        project_id = options['project_id']
        output_file = options['output_file']
        export_format = options['format']
        
        try:
            project = Project.objects.get(id=project_id)
            tasks = Task.objects.filter(project=project).prefetch_related('annotations')
            
            export_data = []
            for task in tasks:
                task_extension = getattr(task, 'taskextension', None)
                
                for annotation in task.annotations.all():
                    if export_format == 'json':
                        item = {
                            'task_id': task.id,
                            'document_name': task_extension.document_name if task_extension else '',
                            'ocr_content': task.data.get('ocr_content', ''),
                            'annotation_result': annotation.result,
                            'created_at': annotation.created_at.isoformat(),
                            'annotator': annotation.completed_by.username if annotation.completed_by else None
                        }
                    else:  # CSV format
                        # 解析annotation result，转换为实体列表
                        entities = self.parse_annotation_result(annotation.result)
                        for entity in entities:
                            item = {
                                'task_id': task.id,
                                'document_name': task_extension.document_name if task_extension else '',
                                'entity_text': entity['text'],
                                'entity_type': entity['type'],
                                'start_offset': entity['start'],
                                'end_offset': entity['end'],
                                'annotator': annotation.completed_by.username if annotation.completed_by else None
                            }
                            export_data.append(item)
                        continue
                    
                    export_data.append(item)
            
            # 保存文件
            if export_format == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'project_id': project_id,
                        'project_title': project.title,
                        'export_time': datetime.now().isoformat(),
                        'annotations_count': len(export_data),
                        'annotations': export_data
                    }, f, ensure_ascii=False, indent=2)
            else:
                import csv
                if export_data:
                    with open(output_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=export_data[0].keys())
                        writer.writeheader()
                        writer.writerows(export_data)
            
            self.stdout.write(
                self.style.SUCCESS(f'成功导出 {len(export_data)} 条标注结果到 {output_file}')
            )
            
        except Project.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'项目 {project_id} 不存在')
            )

    def parse_annotation_result(self, result):
        """解析标注结果，提取实体信息"""
        entities = []
        for item in result:
            if item.get('type') == 'labels':
                entities.append({
                    'text': item['value']['text'],
                    'type': item['value']['labels'][0] if item['value']['labels'] else '',
                    'start': item['value']['start'],
                    'end': item['value']['end']
                })
        return entities
```

## 5. 前端定制

### 5.1 自定义CSS样式
```css
/* static/css/sensitive_entity_annotation.css */
.sensitive-entity-panel {
    padding: 15px;
    background: #f8f9fa;
    border-radius: 5px;
    margin-bottom: 20px;
}

.category-group {
    margin-bottom: 15px;
    padding: 10px;
    background: white;
    border-radius: 3px;
    border-left: 4px solid #007bff;
}

.category-group h4 {
    margin: 0 0 10px 0;
    color: #495057;
    font-size: 14px;
    font-weight: 600;
}

.label-item {
    display: inline-block;
    margin: 3px 5px 3px 0;
    padding: 4px 8px;
    background: #e9ecef;
    border-radius: 3px;
    font-size: 12px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.label-item:hover {
    background: #dee2e6;
}

.label-item.selected {
    background: #007bff;
    color: white;
}

.annotation-preview {
    background: #fff;
    border: 1px solid #dee2e6;
    border-radius: 5px;
    padding: 15px;
    margin-top: 15px;
}

.entity-list {
    max-height: 300px;
    overflow-y: auto;
}

.entity-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 5px 10px;
    margin: 3px 0;
    background: #f8f9fa;
    border-radius: 3px;
    font-size: 12px;
}

.entity-text {
    font-weight: 500;
    color: #495057;
}

.entity-type {
    padding: 2px 6px;
    background: #6c757d;
    color: white;
    border-radius: 2px;
    font-size: 10px;
}

.delete-btn {
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 2px;
    padding: 2px 6px;
    font-size: 10px;
    cursor: pointer;
}

/* 快捷键提示 */
.hotkey-help {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 10px;
    border-radius: 5px;
    font-size: 12px;
    z-index: 1000;
}
```

### 5.2 JavaScript增强
```javascript
// static/js/sensitive_entity_annotation.js
(function() {
    'use strict';
    
    // 实体类别快捷键映射
    const HOTKEY_MAPPING = {
        '1': 'FullName',
        '2': 'FirstName', 
        '3': 'LastName',
        '4': 'Address',
        '5': 'StreetNumber',
        '6': 'StreetName',
        '7': 'City',
        '8': 'State',
        '9': 'ZipCode',
        'q': 'InvoiceNumber',
        'w': 'CompanyName',
        'e': 'CheckNumber',
        'r': 'Date',
        't': 'MilitaryAddress'
    };
    
    // 初始化增强功能
    function initSensitiveEntityEnhancements() {
        addHotkeySupport();
        addEntityCounter();
        addProgressTracker();
        addValidationHelper();
    }
    
    // 添加快捷键支持
    function addHotkeySupport() {
        document.addEventListener('keydown', function(e) {
            // 仅在选择了文本时触发
            if (window.getSelection().toString() && HOTKEY_MAPPING[e.key]) {
                e.preventDefault();
                applyEntityLabel(HOTKEY_MAPPING[e.key]);
            }
        });
    }
    
    // 应用实体标签
    function applyEntityLabel(labelType) {
        const selection = window.getSelection();
        if (!selection.toString()) return;
        
        // 触发Label Studio的标注事件
        const event = new CustomEvent('labelApply', {
            detail: {
                labelType: labelType,
                text: selection.toString(),
                range: selection.getRangeAt(0)
            }
        });
        document.dispatchEvent(event);
    }
    
    // 添加实体计数器
    function addEntityCounter() {
        const counterEl = document.createElement('div');
        counterEl.id = 'entity-counter';
        counterEl.className = 'entity-counter';
        counterEl.innerHTML = '已标注实体: <span class="count">0</span>';
        
        // 插入到合适位置
        const targetEl = document.querySelector('.lsf-annotation-tab') || document.body;
        targetEl.appendChild(counterEl);
        
        // 监听标注变化
        document.addEventListener('annotationUpdate', updateEntityCounter);
    }
    
    // 更新实体计数
    function updateEntityCounter() {
        const annotations = document.querySelectorAll('.htx-annotation');
        const countEl = document.querySelector('#entity-counter .count');
        if (countEl) {
            countEl.textContent = annotations.length;
        }
    }
    
    // 添加进度跟踪
    function addProgressTracker() {
        const progressEl = document.createElement('div');
        progressEl.className = 'progress-tracker';
        progressEl.innerHTML = `
            <div class="progress-bar">
                <div class="progress-fill" style="width: 0%"></div>
            </div>
            <div class="progress-text">进度: 0%</div>
        `;
        
        document.body.appendChild(progressEl);
        
        // 定期更新进度
        setInterval(updateProgress, 1000);
    }
    
    // 更新进度
    function updateProgress() {
        // 根据标注完成情况计算进度
        const requiredEntities = countRequiredEntities();
        const annotatedEntities = countAnnotatedEntities();
        const progress = requiredEntities > 0 ? (annotatedEntities / requiredEntities) * 100 : 0;
        
        const progressFill = document.querySelector('.progress-fill');
        const progressText = document.querySelector('.progress-text');
        
        if (progressFill && progressText) {
            progressFill.style.width = `${Math.min(progress, 100)}%`;
            progressText.textContent = `进度: ${Math.round(progress)}%`;
        }
    }
    
    // 计算需要标注的实体数量（基于MASK标记）
    function countRequiredEntities() {
        const content = document.querySelector('[name="text"]')?.textContent || '';
        const maskMatches = content.match(/\[MASK_[^\]]+\]/g) || [];
        return maskMatches.length;
    }
    
    // 计算已标注的实体数量
    function countAnnotatedEntities() {
        return document.querySelectorAll('.htx-annotation').length;
    }
    
    // 添加验证助手
    function addValidationHelper() {
        const helperEl = document.createElement('div');
        helperEl.className = 'validation-helper';
        helperEl.innerHTML = `
            <button type="button" onclick="validateAnnotation()">验证标注</button>
            <div class="validation-results"></div>
        `;
        
        document.body.appendChild(helperEl);
    }
    
    // 验证标注
    window.validateAnnotation = function() {
        const results = [];
        
        // 检查是否有未标注的MASK
        const content = document.querySelector('[name="text"]')?.textContent || '';
        const masks = content.match(/\[MASK_[^\]]+\]/g) || [];
        const annotations = document.querySelectorAll('.htx-annotation');
        
        if (masks.length > annotations.length) {
            results.push(`⚠️ 发现 ${masks.length - annotations.length} 个可能未标注的MASK`);
        }
        
        // 检查标注的一致性
        const entityTypes = Array.from(annotations).map(el => el.dataset.label);
        const duplicates = findDuplicateEntities(entityTypes);
        if (duplicates.length > 0) {
            results.push(`⚠️ 发现重复标注: ${duplicates.join(', ')}`);
        }
        
        // 显示验证结果
        const resultsEl = document.querySelector('.validation-results');
        if (resultsEl) {
            resultsEl.innerHTML = results.length > 0 
                ? results.map(r => `<div>${r}</div>`).join('')
                : '<div style="color: green;">✅ 标注验证通过</div>';
        }
    };
    
    // 查找重复实体
    function findDuplicateEntities(entities) {
        const seen = new Set();
        const duplicates = [];
        
        entities.forEach(entity => {
            if (seen.has(entity)) {
                duplicates.push(entity);
            } else {
                seen.add(entity);
            }
        });
        
        return [...new Set(duplicates)];
    }
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSensitiveEntityEnhancements);
    } else {
        initSensitiveEntityEnhancements();
    }
})();
```

## 6. 集成配置

### 6.1 settings.py配置
```python
# label_studio/settings/custom.py
from label_studio.core.settings.base import *

# 添加自定义应用
INSTALLED_APPS += [
    'apps.sensitive_entity_annotation',
]

# 自定义中间件
MIDDLEWARE += [
    'apps.sensitive_entity_annotation.middleware.SensitiveDataMiddleware',
]

# 敏感实体标注配置
SENSITIVE_ENTITY_CONFIG = {
    'MAX_BATCH_SIZE': 1000,  # 最大批量导入大小
    'DEFAULT_PRIORITY': 'normal',
    'ENABLE_AUTO_VALIDATION': True,
    'QUALITY_THRESHOLD': 0.95,
    'EXPORT_FORMATS': ['json', 'csv', 'xlsx'],
}

# 静态文件配置
STATICFILES_DIRS += [
    os.path.join(BASE_DIR, 'apps/sensitive_entity_annotation/static'),
]

# 模板配置
TEMPLATES[0]['DIRS'] += [
    os.path.join(BASE_DIR, 'apps/sensitive_entity_annotation/templates'),
]
```

### 6.2 URL配置
```python
# apps/sensitive_entity_annotation/urls.py
from django.urls import path
from . import views

app_name = 'sensitive_entity_annotation'

urlpatterns = [
    path('api/bulk-import/', views.bulk_import_tasks, name='bulk_import_tasks'),
    path('api/export/<int:project_id>/', views.export_annotations, name='export_annotations'),
    path('api/quality-review/<int:annotation_id>/', views.quality_review, name='quality_review'),
    path('api/statistics/<int:user_id>/', views.user_statistics, name='user_statistics'),
]

# 在主urls.py中包含
# path('sensitive-entity/', include('apps.sensitive_entity_annotation.urls')),
```

## 7. 部署集成

### 7.1 Docker集成
```dockerfile
# 在主Dockerfile中添加
COPY apps/sensitive_entity_annotation/ /label-studio/apps/sensitive_entity_annotation/
COPY static/css/sensitive_entity_annotation.css /label-studio/static/css/
COPY static/js/sensitive_entity_annotation.js /label-studio/static/js/

# 安装额外依赖
RUN pip install openpyxl pandas
```

### 7.2 环境变量
```bash
# .env文件添加
SENSITIVE_ENTITY_MAX_BATCH_SIZE=1000
SENSITIVE_ENTITY_ENABLE_AUTO_VALIDATION=true
SENSITIVE_ENTITY_QUALITY_THRESHOLD=0.95
```

这个定制化方案通过配置、扩展和增强的方式，在不修改Label Studio核心代码的前提下，实现了专业的敏感实体标注功能。 