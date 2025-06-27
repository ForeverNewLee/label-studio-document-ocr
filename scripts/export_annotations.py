#!/usr/bin/env python3
"""
敏感实体标注服务 - 标注结果导出脚本
支持多种格式导出标注数据
"""

import requests
import csv
import json
from datetime import datetime
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys
from urllib.parse import urljoin

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnnotationExporter:
    """标注结果导出器"""
    
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
    
    def export_annotations(self, project_id: int) -> Optional[List[Dict[str, Any]]]:
        """导出标注数据"""
        try:
            logger.info(f"📥 从项目 {project_id} 导出标注数据...")
            
            response = requests.get(
                urljoin(self.api_url, f"/api/projects/{project_id}/export"),
                headers=self.headers,
                params={"exportType": "JSON"}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 成功获取 {len(data)} 条标注记录")
                return data
            else:
                logger.error(f"❌ 导出失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 导出过程错误: {e}")
            return None
    
    def save_to_csv(self, data: List[Dict[str, Any]], output_dir: str) -> str:
        """保存为CSV格式"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(output_dir) / f"annotations_export_{timestamp}.csv"
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入标题行
            writer.writerow([
                'Document_Name', 'Entity_Text', 'Entity_Label', 
                'Start_Pos', 'End_Pos', 'Annotator', 'Created_At', 'Task_ID'
            ])
            
            # 写入数据
            for item in data:
                document_name = item['data'].get('document_name', 'unknown')
                task_id = item.get('id', 'unknown')
                created_at = item.get('created_at', '')
                
                # 处理标注结果
                annotations = item.get('annotations', [])
                if not annotations:
                    # 如果没有标注，写一行表示未标注
                    writer.writerow([
                        document_name, '', '', '', '', '', created_at, task_id
                    ])
                    continue
                
                for annotation in annotations:
                    annotator = annotation.get('completed_by', {}).get('email', 'unknown')
                    annotation_created = annotation.get('created_at', '')
                    
                    results = annotation.get('result', [])
                    if not results:
                        # 空标注
                        writer.writerow([
                            document_name, '', '', '', '', annotator, annotation_created, task_id
                        ])
                        continue
                    
                    for result in results:
                        entity_text = result.get('value', {}).get('text', '')
                        entity_label = ','.join(result.get('value', {}).get('labels', []))
                        start_pos = result.get('value', {}).get('start', '')
                        end_pos = result.get('value', {}).get('end', '')
                        
                        writer.writerow([
                            document_name, entity_text, entity_label,
                            start_pos, end_pos, annotator, annotation_created, task_id
                        ])
        
        logger.info(f"✅ CSV导出完成: {output_file}")
        return str(output_file)
    
    def save_to_json(self, data: List[Dict[str, Any]], output_dir: str) -> str:
        """保存为JSON格式"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(output_dir) / f"annotations_export_{timestamp}.json"
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ JSON导出完成: {output_file}")
        return str(output_file)
    
    def save_to_entity_list(self, data: List[Dict[str, Any]], output_dir: str) -> str:
        """保存为实体清单格式（符合标注规范）"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(output_dir) / f"entity_list_{timestamp}.txt"
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("敏感实体标注结果\n")
            f.write("=" * 60 + "\n\n")
            
            for item in data:
                document_name = item['data'].get('document_name', 'unknown')
                f.write(f"文档: {document_name}\n")
                f.write("-" * 40 + "\n")
                
                annotations = item.get('annotations', [])
                if not annotations:
                    f.write("状态: 未标注\n\n")
                    continue
                
                # 收集所有实体
                entities = []
                for annotation in annotations:
                    results = annotation.get('result', [])
                    for result in results:
                        entity_text = result.get('value', {}).get('text', '')
                        labels = result.get('value', {}).get('labels', [])
                        if entity_text and labels:
                            for label in labels:
                                entities.append(f"{entity_text}: {label}")
                
                if entities:
                    f.write("实体清单（冒号后的标签请查表）:\n")
                    for entity in sorted(entities):
                        f.write(f"{entity}\n")
                else:
                    f.write("状态: 已标注但无实体\n")
                
                f.write("\n")
        
        logger.info(f"✅ 实体清单导出完成: {output_file}")
        return str(output_file)
    
    def generate_statistics(self, data: List[Dict[str, Any]], output_dir: str) -> str:
        """生成统计报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(output_dir) / f"statistics_report_{timestamp}.txt"
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 统计数据
        total_tasks = len(data)
        annotated_tasks = sum(1 for item in data if item.get('annotations'))
        completed_tasks = sum(1 for item in data 
                            if item.get('annotations') and 
                            any(ann.get('was_cancelled', False) == False 
                                for ann in item['annotations']))
        
        # 实体类型统计
        entity_stats = {}
        total_entities = 0
        
        for item in data:
            annotations = item.get('annotations', [])
            for annotation in annotations:
                results = annotation.get('result', [])
                for result in results:
                    labels = result.get('value', {}).get('labels', [])
                    for label in labels:
                        entity_stats[label] = entity_stats.get(label, 0) + 1
                        total_entities += 1
        
        # 写入报告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("敏感实体标注统计报告\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("任务统计:\n")
            f.write("-" * 30 + "\n")
            f.write(f"总任务数: {total_tasks}\n")
            f.write(f"已标注任务: {annotated_tasks}\n")
            f.write(f"完成任务: {completed_tasks}\n")
            f.write(f"标注进度: {annotated_tasks/total_tasks*100:.1f}%\n\n")
            
            f.write("实体统计:\n")
            f.write("-" * 30 + "\n")
            f.write(f"标注实体总数: {total_entities}\n")
            f.write(f"实体类型数: {len(entity_stats)}\n\n")
            
            if entity_stats:
                f.write("各类型实体数量:\n")
                for label, count in sorted(entity_stats.items(), 
                                         key=lambda x: x[1], reverse=True):
                    percentage = count / total_entities * 100
                    f.write(f"  {label}: {count} ({percentage:.1f}%)\n")
        
        logger.info(f"✅ 统计报告生成完成: {output_file}")
        return str(output_file)
    
    def run_export(self, project_id: int, output_dir: str, 
                   formats: List[str]) -> List[str]:
        """执行完整导出流程"""
        logger.info(f"🚀 开始标注结果导出流程")
        
        # 1. 验证连接
        if not self.verify_connection():
            return []
        
        # 2. 检查项目
        project_info = self.get_project_info(project_id)
        if not project_info:
            logger.error(f"❌ 项目 {project_id} 不存在或无权限访问")
            return []
        
        logger.info(f"📋 目标项目: {project_info.get('title', 'Unknown')} (ID: {project_id})")
        
        # 3. 导出数据
        data = self.export_annotations(project_id)
        if not data:
            return []
        
        # 4. 保存为各种格式
        output_files = []
        
        for format_type in formats:
            try:
                if format_type == 'csv':
                    file_path = self.save_to_csv(data, output_dir)
                    output_files.append(file_path)
                elif format_type == 'json':
                    file_path = self.save_to_json(data, output_dir)
                    output_files.append(file_path)
                elif format_type == 'entity_list':
                    file_path = self.save_to_entity_list(data, output_dir)
                    output_files.append(file_path)
                elif format_type == 'statistics':
                    file_path = self.generate_statistics(data, output_dir)
                    output_files.append(file_path)
                else:
                    logger.warning(f"⚠️ 不支持的格式: {format_type}")
            except Exception as e:
                logger.error(f"❌ 导出格式 {format_type} 失败: {e}")
        
        logger.info(f"🎉 导出完成! 共生成 {len(output_files)} 个文件")
        return output_files


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='导出Label Studio项目的标注结果',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
    # 导出为CSV格式
    python scripts/export_annotations.py --api-token YOUR_TOKEN --project-id 1 --format csv
    
    # 导出多种格式
    python scripts/export_annotations.py --api-token YOUR_TOKEN --project-id 1 --format csv,json,entity_list,statistics
    
    # 指定输出目录
    python scripts/export_annotations.py --api-token YOUR_TOKEN --project-id 1 --format csv --output-dir ./exports/

支持的导出格式:
    csv         - CSV表格格式（便于分析）
    json        - JSON原始格式（完整数据）
    entity_list - 实体清单格式（符合标注规范）
    statistics  - 统计报告（进度和分布）
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
        help='项目ID (必需)'
    )
    parser.add_argument(
        '--format', 
        default='csv,entity_list,statistics',
        help='导出格式，多个用逗号分隔 (默认: csv,entity_list,statistics)'
    )
    parser.add_argument(
        '--output-dir', 
        default='./exports',
        help='输出目录 (默认: ./exports)'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='显示详细日志'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 解析格式列表
    formats = [fmt.strip() for fmt in args.format.split(',')]
    
    # 执行导出
    exporter = AnnotationExporter(args.api_url, args.api_token)
    output_files = exporter.run_export(args.project_id, args.output_dir, formats)
    
    if output_files:
        print("\n生成的文件:")
        for file_path in output_files:
            print(f"  📄 {file_path}")
    
    sys.exit(0 if output_files else 1)


if __name__ == "__main__":
    main() 