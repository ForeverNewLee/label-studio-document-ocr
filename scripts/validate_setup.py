#!/usr/bin/env python3
"""
敏感实体标注服务 - 环境验证脚本
验证项目配置和依赖是否正确
"""

import sys
from pathlib import Path
import importlib


def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    version = sys.version_info
    if version >= (3, 8):
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python版本过低: {version.major}.{version.minor}.{version.micro} (需要 >= 3.8)")
        return False


def check_required_packages():
    """检查必需的Python包"""
    print("\n🔍 检查Python包依赖...")
    
    required_packages = {
        'requests': '网络请求库',
        'pathlib': '路径处理库',
        'json': 'JSON处理库',
        'csv': 'CSV处理库',
        'argparse': '命令行参数解析',
        'logging': '日志库',
        'subprocess': '子进程库',
        'urllib.parse': 'URL解析库'
    }
    
    all_available = True
    for package, description in required_packages.items():
        try:
            importlib.import_module(package)
            print(f"✅ {package}: {description}")
        except ImportError:
            print(f"❌ {package}: {description} - 未安装")
            all_available = False
    
    return all_available


def check_file_structure():
    """检查文件结构"""
    print("\n🔍 检查项目文件结构...")
    
    required_files = {
        'configs/annotation_template.xml': '标注模板文件',
        'demo_data/document_ocr_demo_0.txt': 'Demo数据文件1',
        'demo_data/document_ocr_demo_1.txt': 'Demo数据文件2', 
        'demo_data/document_ocr_demo_2.txt': 'Demo数据文件3',
        'scripts/import_ocr_documents.py': '数据导入脚本',
        'scripts/export_annotations.py': '数据导出脚本',
        'scripts/setup_project.py': '项目设置脚本',
        'scripts/start_service.py': '服务启动脚本',
        'requirements.txt': '依赖文件'
    }
    
    all_exist = True
    for file_path, description in required_files.items():
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size if path.is_file() else "目录"
            print(f"✅ {file_path}: {description} ({size} bytes)")
        else:
            print(f"❌ {file_path}: {description} - 文件不存在")
            all_exist = False
    
    return all_exist


def check_directories():
    """检查必要目录"""
    print("\n🔍 检查项目目录结构...")
    
    required_dirs = [
        'scripts',
        'configs', 
        'demo_data',
        'exports',
        'docs',
        'docs/requirements',
        'docs/product_design',
        'docs/technical'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            file_count = len(list(path.iterdir())) if path.exists() else 0
            print(f"✅ {dir_path}/ - {file_count} 个文件")
        else:
            print(f"❌ {dir_path}/ - 目录不存在")
            all_exist = False
    
    return all_exist


def validate_demo_data():
    """验证demo数据内容"""
    print("\n🔍 验证demo数据内容...")
    
    demo_files = [
        'demo_data/document_ocr_demo_0.txt',
        'demo_data/document_ocr_demo_1.txt', 
        'demo_data/document_ocr_demo_2.txt'
    ]
    
    all_valid = True
    for demo_file in demo_files:
        path = Path(demo_file)
        if path.exists():
            content = path.read_text(encoding='utf-8')
            if content.strip():
                lines = len(content.split('\n'))
                has_mask = '[MASK_' in content
                print(f"✅ {demo_file}: {lines} 行, 包含MASK: {has_mask}")
            else:
                print(f"⚠️ {demo_file}: 文件为空")
                all_valid = False
        else:
            print(f"❌ {demo_file}: 文件不存在")
            all_valid = False
    
    return all_valid


def validate_annotation_template():
    """验证标注模板"""
    print("\n🔍 验证标注模板...")
    
    template_path = Path('configs/annotation_template.xml')
    if not template_path.exists():
        print("❌ 标注模板文件不存在")
        return False
    
    content = template_path.read_text(encoding='utf-8')
    
    # 检查关键元素
    checks = {
        '<View>': 'View根元素',
        '<Labels': 'Labels标签定义',
        '<Text name="text"': '文本显示组件',
        'hotkey=': '快捷键配置',
        'FullName': '姓名标签',
        'Address': '地址标签',
        'Date': '日期标签'
    }
    
    all_valid = True
    for element, description in checks.items():
        if element in content:
            print(f"✅ {description}: 已配置")
        else:
            print(f"❌ {description}: 缺失")
            all_valid = False
    
    return all_valid


def main():
    """主验证函数"""
    print("🚀 敏感实体标注服务 - 环境验证")
    print("=" * 50)
    
    checks = [
        check_python_version(),
        check_required_packages(),
        check_directories(),
        check_file_structure(),
        validate_demo_data(),
        validate_annotation_template()
    ]
    
    print("\n" + "=" * 50)
    print("📊 验证结果汇总")
    print("=" * 50)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"🎉 验证通过: {passed}/{total} 项检查成功")
        print("\n✅ 环境配置正确，可以开始使用敏感实体标注服务")
        print("\n下一步:")
        print("1. 运行 python scripts/start_service.py 启动服务")
        print("2. 访问 http://localhost:8080 完成初始设置")
        print("3. 获取API Token后运行项目设置脚本")
        return True
    else:
        print(f"⚠️ 验证失败: {passed}/{total} 项检查成功，{total-passed} 项失败")
        print("\n❌ 环境配置存在问题，请根据上述错误信息进行修复")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 