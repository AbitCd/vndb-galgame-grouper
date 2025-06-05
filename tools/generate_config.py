"""
生成配置文件的辅助脚本

使用方法:
    在项目根目录运行:
        python -m tools.generate_config config --type type --output config_example
将在当前目录生成 config.json 或 config.ini
"""

import os
import sys
from pathlib import Path
import argparse
import subprocess

# 添加项目根目录到PYTHONPATH
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.templates.config_example import generate_json_config, generate_ini_config

def generate_config(config_type, output_path):
    """生成配置文件"""
    if config_type == 'json':
        generate_json_config(output_path)
    else:
        generate_ini_config(output_path)

def start_api_server(host, port):
    """启动API服务器"""
    api_module_path = os.path.join(project_root, 'src', 'api', 'server.py')
    subprocess.run([sys.executable, api_module_path, '--host', host, '--port', str(port)])

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VNDB处理工具辅助脚本")
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 生成配置命令
    config_parser = subparsers.add_parser('config', help='生成配置文件')
    config_parser.add_argument('--type', choices=['json', 'ini'], default='json', help='配置文件类型 (默认: json)')
    config_parser.add_argument('--output', type=str, default='config_example', help='输出文件名 (不含扩展名)')
    
    # 启动服务器命令
    server_parser = subparsers.add_parser('server', help='启动API服务器')
    server_parser.add_argument('--host', default='127.0.0.1', help='服务器主机 (默认: 127.0.0.1)')
    server_parser.add_argument('--port', type=int, default=8080, help='服务器端口 (默认: 8080)')
    
    args = parser.parse_args()
    
    if args.command == 'config':
        output_path = f"{args.output}.{args.type}"
        generate_config(args.type, output_path)
    elif args.command == 'server':
        start_api_server(args.host, args.port)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()