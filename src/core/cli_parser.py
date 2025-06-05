"""
命令行参数解析器
"""
import argparse
from typing import Dict, Any
# 删除未使用的导入
# from typing import Optional

def parse_args() -> Dict[str, Any]:
    """
    解析命令行参数
    
    返回:
        Dict[str, Any]: 解析后的参数字典
    """
    parser = argparse.ArgumentParser(description="VNDB文件夹处理工具")
    
    # 创建输入方式互斥组
    input_mode = parser.add_mutually_exclusive_group()
    input_mode.add_argument('--cli', action='store_true', help='使用命令行交互输入')
    input_mode.add_argument('--gui', action='store_true', help='使用图形界面输入（默认）')
    input_mode.add_argument('--config', type=str, help='使用配置文件输入，支持.json和.ini格式')
    input_mode.add_argument('--api', action='store_true', help='使用API输入（从标准输入读取JSON）')
    
    # 直接参数组
    direct_group = parser.add_argument_group('直接参数')
    direct_group.add_argument('--folder', type=str, help='待处理的文件夹路径')
    direct_group.add_argument('--regex', type=str, help='用于过滤目录名的正则表达式')
    direct_group.add_argument('--debug', action='store_true', help='启用调试模式')
    direct_group.add_argument('--no-api-cache', action='store_true', help='禁用API缓存')
    direct_group.add_argument('--no-group-cache', action='store_true', help='禁用分组缓存')
    direct_group.add_argument('--no-vn-group', action='store_true', help='禁用VisualNovel/NotMatched分组')
    direct_group.add_argument('--no-tag-group', action='store_true', help='禁用标签分组')
    direct_group.add_argument('--tag-field', type=str, help='要分组的标签字段')
    direct_group.add_argument('--rename-original', action='store_true', help='将分组文件夹名替换为原名')
    direct_group.add_argument('--normalize', action='store_true', help='规范化文件夹名称')
    direct_group.add_argument('--strict-normalize', action='store_true', help='严格规范化（仅保留通用名）')

    args = parser.parse_args()

    # 验证参数依赖关系
    if args.strict_normalize and not args.normalize:
        parser.error("使用--strict-normalize必须同时启用--normalize")
    
    if args.rename_original and not args.tag_field:
        parser.error("使用--rename-original必须同时指定--tag-field")
    
    if args.tag_field and args.no_tag_group:
        parser.error("指定--tag-field时不能使用--no-tag-group")

    # 检查输入模式和直接参数的互斥性
    has_input_mode = any([args.cli, args.gui, args.config, args.api])
    has_direct_args = any([
        args.folder, args.regex, args.debug, args.no_api_cache,
        args.no_group_cache, args.no_vn_group,
        args.no_tag_group, args.tag_field, args.rename_original,
        args.normalize, args.strict_normalize
    ])

    if has_input_mode and has_direct_args:
        parser.error("不能同时使用输入模式参数和直接参数")

    # 返回处理后的参数字典
    return vars(args)