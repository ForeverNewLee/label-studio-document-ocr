#!/usr/bin/env python3
"""
敏感实体标注服务 - 一键启动脚本
检查环境、启动Label Studio服务并进行验证
"""

import subprocess
import sys
import time
import requests
import argparse
import logging
from pathlib import Path
from typing import Optional
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServiceStarter:
    """服务启动管理器"""
    
    def __init__(self, port: int = 8080, host: str = "0.0.0.0"):
        self.port = port
        self.host = host
        self.api_url = f"http://localhost:{port}"
    
    def check_prerequisites(self) -> bool:
        """检查环境依赖"""
        logger.info("🔍 检查环境依赖...")
        
        # 检查Python版本
        if sys.version_info < (3, 8):
            logger.error("❌ 需要Python 3.8或更高版本")
            return False
        
        logger.info(f"✅ Python版本: {sys.version.split()[0]}")
        
        # 检查label-studio是否安装
        if not shutil.which("label-studio"):
            logger.error("❌ Label Studio未安装")
            logger.info("请运行: pip install label-studio")
            return False
        
        logger.info("✅ Label Studio已安装")
        
        # 检查必要目录
        required_dirs = ["scripts", "configs", "demo_data", "exports"]
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                logger.warning(f"⚠️ 创建目录: {dir_name}")
                dir_path.mkdir(parents=True, exist_ok=True)
        
        # 检查配置文件
        template_file = Path("configs/annotation_template.xml")
        if not template_file.exists():
            logger.error("❌ 标注模板文件不存在: configs/annotation_template.xml")
            return False
        
        logger.info("✅ 标注模板文件存在")
        
        return True
    
    def check_port_available(self) -> bool:
        """检查端口是否可用"""
        try:
            response = requests.get(self.api_url, timeout=2)
            logger.warning(f"⚠️ 端口 {self.port} 已被占用，可能是现有的Label Studio实例")
            return False
        except requests.exceptions.RequestException:
            logger.info(f"✅ 端口 {self.port} 可用")
            return True
    
    def start_label_studio(self, background: bool = True) -> Optional[subprocess.Popen]:
        """启动Label Studio服务"""
        logger.info(f"🚀 启动Label Studio服务 (端口: {self.port})")
        
        cmd = [
            "label-studio",
            "start",
            "--host", self.host,
            "--port", str(self.port),
            "--log-level", "INFO"
        ]
        
        try:
            if background:
                # 后台启动
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                logger.info(f"✅ Label Studio已在后台启动 (PID: {process.pid})")
                return process
            else:
                # 前台启动
                logger.info("📌 前台启动Label Studio (Ctrl+C退出)")
                subprocess.run(cmd)
                return None
                
        except Exception as e:
            logger.error(f"❌ 启动Label Studio失败: {e}")
            return None
    
    def wait_for_service(self, timeout: int = 30) -> bool:
        """等待服务启动完成"""
        logger.info(f"⏳ 等待服务启动完成 (超时: {timeout}秒)")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f"{self.api_url}/api/",
                    timeout=5
                )
                if response.status_code == 200:
                    logger.info("✅ 服务启动成功")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
            logger.info("⏳ 继续等待...")
        
        logger.error("❌ 服务启动超时")
        return False
    
    def show_service_info(self) -> None:
        """显示服务信息"""
        logger.info("🎉 敏感实体标注服务已就绪!")
        print("\n" + "=" * 60)
        print("🌐 服务信息")
        print("=" * 60)
        print(f"📍 服务地址: {self.api_url}")
        print(f"📋 管理界面: {self.api_url}/projects/")
        print(f"🔑 API文档: {self.api_url}/docs/")
        print()
        print("🛠️ 快速开始")
        print("=" * 60)
        print("1. 访问管理界面创建账户")
        print("2. 获取API Token (Account & Settings)")
        print("3. 创建项目:")
        print(f"   python scripts/setup_project.py --api-token YOUR_TOKEN")
        print("4. 导入数据:")
        print(f"   python scripts/import_ocr_documents.py --api-token YOUR_TOKEN --project-id PROJECT_ID")
        print("5. 开始标注工作")
        print()
        print("📚 更多帮助")
        print("=" * 60)
        print("- 查看文档: docs/")
        print("- 标注示例: docs/product_design/annotation_examples.md")
        print("- 技术文档: docs/technical/")
        print("=" * 60 + "\n")
    
    def run_startup(self, background: bool = True, skip_checks: bool = False) -> bool:
        """执行完整启动流程"""
        logger.info("🚀 开始启动敏感实体标注服务")
        
        # 1. 检查环境
        if not skip_checks and not self.check_prerequisites():
            return False
        
        # 2. 检查端口
        if not self.check_port_available():
            if not skip_checks:
                return False
        
        # 3. 启动服务
        process = self.start_label_studio(background)
        if background and not process:
            return False
        
        # 4. 等待服务就绪
        if background:
            if not self.wait_for_service():
                if process:
                    process.terminate()
                return False
        
        # 5. 显示服务信息
        if background:
            self.show_service_info()
        
        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='启动敏感实体标注服务',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
    # 后台启动服务
    python scripts/start_service.py
    
    # 前台启动（用于调试）
    python scripts/start_service.py --foreground
    
    # 自定义端口
    python scripts/start_service.py --port 8090
    
    # 跳过环境检查（如果确认环境正常）
    python scripts/start_service.py --skip-checks

启动后的操作:
    1. 访问 http://localhost:8080 创建管理员账户
    2. 获取API Token
    3. 使用setup_project.py创建项目
    4. 使用import_ocr_documents.py导入数据
        """
    )
    
    parser.add_argument(
        '--port', 
        type=int,
        default=8080,
        help='服务端口 (默认: 8080)'
    )
    parser.add_argument(
        '--host', 
        default='0.0.0.0',
        help='绑定主机地址 (默认: 0.0.0.0)'
    )
    parser.add_argument(
        '--foreground', 
        action='store_true',
        help='前台启动（非后台运行）'
    )
    parser.add_argument(
        '--skip-checks', 
        action='store_true',
        help='跳过环境检查'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='显示详细日志'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 启动服务
    starter = ServiceStarter(port=args.port, host=args.host)
    success = starter.run_startup(
        background=not args.foreground,
        skip_checks=args.skip_checks
    )
    
    if not success:
        logger.error("❌ 服务启动失败")
        sys.exit(1)
    
    if args.foreground:
        logger.info("🔄 前台模式运行中...")
    else:
        logger.info("✅ 服务已在后台运行")


if __name__ == "__main__":
    main() 