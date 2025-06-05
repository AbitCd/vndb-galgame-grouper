"""
生成配置文件示例
"""
import json
import argparse

def generate_json_config(output_path: str):
    """
    生成JSON格式的配置文件示例
    基于UserInputs模型的默认配置
    """
    config = {
        # 基础配置
        "debug_mode": False,
        "regex_filter": "",
        
        # 缓存操作和设置
        "clear_cache": False,
        "api_cache": True,
        "group_cache": True,
        
        # 文件夹路径
        "folder_path": "",
        
        # 分组设置
        "do_vn_group": True,
        "do_tag_grouping": False,
        "tag_group_field": "",
        "rename_to_original": False,
        
        # 命名规范
        "normalize_name": False,
        "normalize_strict": False,
        
        # 模糊匹配设置
        "enable_fuzzy_match": True,
        "fuzzy_match_threshold": 0.4,
        
        # # 可以自定义参数
        # "custom_params": {}
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"JSON配置文件示例已生成: {output_path}")

def generate_ini_config(output_path: str):
    """
    生成INI格式的配置文件示例
    基于UserInputs模型的默认配置
    """
    config = """[UserInputs]
# 基础配置
debug_mode = False
regex_filter = 

# 缓存操作和设置
clear_cache = False
api_cache = True
group_cache = True

# 文件夹路径
folder_path = 

# 分组设置
do_vn_group = True
do_tag_grouping = False
# 可用的分组字段：
#   artist
#   character_designer
#   composer
#   developers
#   director
#   editor
#   quality_assurance
#   scenario
#   staff
#   translator
#   vocals
#   voice_actor
tag_group_field = 
rename_to_original = False

# 命名规范
normalize_name = False
normalize_strict = False

# 模糊匹配设置
# enable_fuzzy_match: 是否启用模糊匹配
# fuzzy_match_threshold: 模糊匹配阈值(0-1之间)
enable_fuzzy_match = True
fuzzy_match_threshold = 0.4

# 自定义参数
# custom_params可以在此处添加自定义的键值对
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(config)

    print(f"INI配置文件示例已生成: {output_path}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="生成配置文件示例")
    parser.add_argument('--type', choices=['json', 'ini'], default='json', help='配置文件类型 (默认: json)')
    parser.add_argument('--output', type=str, default='config_example', help='输出文件名 (不含扩展名)')

    args = parser.parse_args()

    # 生成文件路径
    output_path = f"{args.output}.{args.type}"

    # 生成配置文件
    if args.type == 'json':
        generate_json_config(output_path)
    else:
        generate_ini_config(output_path)

if __name__ == "__main__":
    main()