#!/usr/bin/env python3
"""
敏感实体标注服务 - 项目设置脚本
自动创建Label Studio项目并配置标注模板
"""

import requests
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import sys
from urllib.parse import urljoin

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProjectSetup:
    """项目设置管理器"""
    
    def __init__(self, api_url: str, api_token: str):
        self.api_url = api_url.rstrip('/')
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        }
    
    def verify_connection(self) -> bool:
        """验证API连接"""
        try:
            response = requests.get(
                urljoin(self.api_url, "/api/"),
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                logger.info("✅ API连接验证成功")
                return True
            else:
                logger.error(f"❌ API连接失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 连接错误: {e}")
            return False
    
    def load_annotation_template(self, template_path: str) -> Optional[str]:
        """加载标注模板"""
        try:
            template_file = Path(template_path)
            if not template_file.exists():
                logger.error(f"❌ 模板文件不存在: {template_path}")
                return None
            
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read().strip()
            
            logger.info(f"✅ 加载标注模板: {template_file.name}")
            return template_content
            
        except Exception as e:
            logger.error(f"❌ 加载模板失败: {e}")
            return None
    
    def create_project(self, project_name: str, description: str, 
                      annotation_template: str) -> Optional[Dict[str, Any]]:
        """创建新项目"""
        try:
            project_data = {
                "title": project_name,
                "description": description,
                "label_config": annotation_template,
                "expert_instruction": """
标注指导说明：

1. 任务目标：识别文档中的所有敏感实体并进行分类标注
2. 标注对象：包括被[MASK]遮挡的和未遮挡的敏感信息
3. 标注方法：选择文本片段后，使用快捷键或点击标签进行分类

重点关注：
- 人名信息（完整姓名、名字、姓氏）
- 地址信息（完整地址及各组成部分）
- 证件号码（发票号、公司名称、支票号等）
- 时间信息（日期、军事地址等）

标注质量要求：
- 准确识别所有敏感实体
- 正确分类每个实体类型
- 保持标注一致性
                """.strip(),
                "show_instruction": True,
                "show_skip_button": True,
                "enable_empty_annotation": True,
                "show_annotation_history": True,
                "maximum_annotations": 1,
                "sampling": "Sequential"
            }
            
            logger.info(f"📋 创建项目: {project_name}")
            
            response = requests.post(
                urljoin(self.api_url, "/api/projects/"),
                headers=self.headers,
                json=project_data
            )
            
            if response.status_code == 201:
                project = response.json()
                logger.info(f"✅ 项目创建成功，ID: {project['id']}")
                return project
            else:
                logger.error(f"❌ 项目创建失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 创建项目错误: {e}")
            return None
    
    def get_existing_projects(self) -> list:
        """获取现有项目列表"""
        try:
            response = requests.get(
                urljoin(self.api_url, "/api/projects/"),
                headers=self.headers
            )
            
            if response.status_code == 200:
                projects = response.json()
                logger.info(f"📋 发现 {len(projects)} 个现有项目")
                return projects
            else:
                logger.error(f"❌ 获取项目列表失败: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 获取项目列表错误: {e}")
            return []
    
    def update_project_config(self, project_id: int, 
                            annotation_template: str) -> bool:
        """更新项目配置"""
        try:
            update_data = {
                "label_config": annotation_template
            }
            
            response = requests.patch(
                urljoin(self.api_url, f"/api/projects/{project_id}/"),
                headers=self.headers,
                json=update_data
            )
            
            if response.status_code == 200:
                logger.info(f"✅ 项目 {project_id} 配置更新成功")
                return True
            else:
                logger.error(f"❌ 更新项目配置失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 更新项目配置错误: {e}")
            return False
    
    def run_setup(self, project_name: str, template_path: str, 
                  update_existing: bool = False) -> Optional[int]:
        """执行完整设置流程"""
        logger.info(f"🚀 开始项目设置流程")
        
        # 1. 验证连接
        if not self.verify_connection():
            return None
        
        # 2. 加载模板
        template_content = self.load_annotation_template(template_path)
        if not template_content:
            return None
        
        # 3. 检查现有项目
        existing_projects = self.get_existing_projects()
        
        # 查找同名项目
        existing_project = None
        for project in existing_projects:
            if project['title'] == project_name:
                existing_project = project
                break
        
        if existing_project:
            if update_existing:
                logger.info(f"🔄 更新现有项目: {project_name} (ID: {existing_project['id']})")
                success = self.update_project_config(existing_project['id'], template_content)
                return existing_project['id'] if success else None
            else:
                logger.warning(f"⚠️ 项目 '{project_name}' 已存在 (ID: {existing_project['id']})")
                logger.info("使用 --update 参数可以更新现有项目配置")
                return existing_project['id']
        
        # 4. 创建新项目
        project = self.create_project(
            project_name=project_name,
            description=f"敏感实体标注项目 - 用于识别和分类文档中的敏感信息",
            annotation_template=template_content
        )
        
        if project:
            project_id = project['id']
            logger.info(f"🎉 项目设置完成!")
            logger.info(f"📍 项目地址: {self.api_url}/projects/{project_id}/")
            logger.info(f"📍 设置页面: {self.api_url}/projects/{project_id}/settings/")
            return project_id
        
        return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='设置Label Studio敏感实体标注项目',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
    # 创建新项目
    python scripts/setup_project.py --api-token YOUR_TOKEN --project-name "敏感实体标注"
    
    # 更新现有项目配置
    python scripts/setup_project.py --api-token YOUR_TOKEN --project-name "敏感实体标注" --update
    
    # 使用自定义模板
    python scripts/setup_project.py --api-token YOUR_TOKEN --project-name "敏感实体标注" --template ./custom_template.xml

后续步骤:
    1. 访问项目页面进行进一步配置
    2. 使用 import_ocr_documents.py 导入数据
    3. 开始标注作业
        """
    )
    
    parser.add_argument(
        '--api-url', 
        default='http://localhost:8080',
        help='Label Studio API地址 (默认: http://localhost:8080)'
    )
    parser.add_argument(
        '--api-token', 
        required=True,
        help='Label Studio API Token (必需)'
    )
    parser.add_argument(
        '--project-name', 
        default='敏感实体标注项目',
        help='项目名称 (默认: "敏感实体标注项目")'
    )
    parser.add_argument(
        '--template', 
        default='./configs/annotation_template.xml',
        help='标注模板文件路径 (默认: ./configs/annotation_template.xml)'
    )
    parser.add_argument(
        '--update', 
        action='store_true',
        help='更新现有项目配置（如果项目已存在）'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='显示详细日志'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 执行设置
    setup = ProjectSetup(args.api_url, args.api_token)
    project_id = setup.run_setup(
        project_name=args.project_name,
        template_path=args.template,
        update_existing=args.update
    )
    
    if project_id:
        print(f"\n🎯 项目设置成功!")
        print(f"📋 项目ID: {project_id}")
        print(f"🔗 项目链接: {args.api_url}/projects/{project_id}/")
        print(f"\n下一步: 使用以下命令导入数据:")
        print(f"python scripts/import_ocr_documents.py --api-token {args.api_token} --project-id {project_id}")
    
    sys.exit(0 if project_id else 1)


if __name__ == "__main__":
    main() 