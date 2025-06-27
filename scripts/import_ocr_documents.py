#!/usr/bin/env python3
"""
敏感实体标注服务 - OCR文档批量导入脚本
基于Label Studio API实现批量任务创建和数据导入
"""

import requests
import json
from pathlib import Path
import argparse
import logging
from typing import List, Dict, Any
import sys
from urllib.parse import urljoin

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OCRDocumentImporter:
    """OCR文档批量导入器"""
    
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
    
    def get_project_info(self, project_id: int) -> Dict[str, Any]:
        """获取项目信息"""
        try:
            response = requests.get(
                urljoin(self.api_url, f"/api/projects/{project_id}"),
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ 获取项目信息失败: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"❌ 获取项目信息错误: {e}")
            return {}
    
    def load_documents(self, data_dir: str) -> List[Dict[str, Any]]:
        """加载OCR文档数据"""
        data_path = Path(data_dir)
        if not data_path.exists():
            logger.error(f"❌ 数据目录不存在: {data_dir}")
            return []
        
        tasks = []
        txt_files = list(data_path.glob("*.txt"))
        
        if not txt_files:
            logger.warning(f"⚠️ 在 {data_dir} 中未找到txt文件")
            return []
        
        logger.info(f"📂 发现 {len(txt_files)} 个文档文件")
        
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if content:
                    task = {
                        "data": {
                            "ocr_content": content,
                            "document_name": txt_file.name,
                            "file_path": str(txt_file)
                        }
                    }
                    tasks.append(task)
                    logger.debug(f"📄 加载文档: {txt_file.name}")
                else:
                    logger.warning(f"⚠️ 空文档: {txt_file.name}")
                    
            except Exception as e:
                logger.error(f"❌ 读取文件失败 {txt_file}: {e}")
        
        logger.info(f"✅ 成功加载 {len(tasks)} 个有效文档")
        return tasks
    
    def import_tasks(self, project_id: int, tasks: List[Dict[str, Any]]) -> bool:
        """批量导入任务"""
        if not tasks:
            logger.error("❌ 没有可导入的任务")
            return False
        
        try:
            logger.info(f"📤 开始导入 {len(tasks)} 个任务到项目 {project_id}...")
            
            response = requests.post(
                urljoin(self.api_url, f"/api/projects/{project_id}/import"),
                headers=self.headers,
                json=tasks
            )
            
            if response.status_code == 201:
                result = response.json()
                imported_count = result.get('task_count', len(tasks))
                logger.info(f"✅ 成功导入 {imported_count} 个任务")
                return True
            else:
                logger.error(f"❌ 导入失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 导入过程错误: {e}")
            return False
    
    def run_import(self, project_id: int, data_dir: str) -> bool:
        """执行完整导入流程"""
        logger.info(f"🚀 开始OCR文档导入流程")
        
        # 1. 验证连接
        if not self.verify_connection():
            return False
        
        # 2. 检查项目
        project_info = self.get_project_info(project_id)
        if not project_info:
            logger.error(f"❌ 项目 {project_id} 不存在或无权限访问")
            return False
        
        logger.info(f"📋 目标项目: {project_info.get('title', 'Unknown')} (ID: {project_id})")
        
        # 3. 加载文档
        tasks = self.load_documents(data_dir)
        if not tasks:
            return False
        
        # 4. 执行导入
        success = self.import_tasks(project_id, tasks)
        
        if success:
            logger.info(f"🎉 导入完成! 项目地址: {self.api_url}/projects/{project_id}/")
        
        return success


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='批量导入OCR文档到Label Studio项目',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
    # 基本用法
    python scripts/import_ocr_documents.py --api-token YOUR_TOKEN --project-id 1
    
    # 指定数据目录
    python scripts/import_ocr_documents.py --api-token YOUR_TOKEN --project-id 1 --data-dir ./custom_data/
    
    # 自定义API地址
    python scripts/import_ocr_documents.py --api-url http://localhost:8080 --api-token YOUR_TOKEN --project-id 1

获取API Token:
    1. 登录Label Studio界面
    2. 点击右上角用户头像 -> Account & Settings
    3. 在Access Token部分复制Token
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
        '--project-id', 
        required=True, 
        type=int,
        help='目标项目ID (必需)'
    )
    parser.add_argument(
        '--data-dir', 
        default='./demo_data',
        help='OCR文档目录 (默认: ./demo_data)'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='显示详细日志'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 执行导入
    importer = OCRDocumentImporter(args.api_url, args.api_token)
    success = importer.run_import(args.project_id, args.data_dir)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 