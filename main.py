"""
主程序入口模块，支持多通道输入（使用Pydantic结构化输入）
"""
import os
import re
import sys
import asyncio
import json
from src.core import config
from src.core.cache_manager import load_cache, save_cache
from src.core.file_utils import safe_print, safe_folder_name, debug_print
from src.core.data_parser import (
    extract_valid_fields, 
    get_most_similar_field, 
    group_by_field, 
    parse_vn_response,
    resolve_role_alias
)
from src.core.folder_operations import (
    divide_into_vn_groups, 
    group_by_tag, 
    recursive_rename
)
from src.core.vndb_api import fetch_vn_info_batch, close_session
from src.core.models import UserInputs
from src.core.input_channels import CliChannel, ConfigFileChannel, ApiChannel
from src.gui.gui_channel import GuiChannel

# 异步主程序逻辑
async def async_main(inputs: UserInputs):
    """异步主程序入口函数"""
    try:
        print_section("VNDB处理工具")
        safe_print("初始化...")

        # 在实际执行前进行参数验证
        try:
            inputs.pre_execution_validation()
            if inputs.debug_mode:
                safe_print("✓ 参数验证通过")
                safe_print(f"文件夹路径: {inputs.folder_path}")
        except ValueError as e:
            safe_print(f"错误: {str(e)}")
            if inputs.debug_mode:
                safe_print("提示: 在GUI模式下，您可以通过界面选择文件夹")
            return
        except Exception as e:
            safe_print(f"发生未知错误: {str(e)}")
            if inputs.debug_mode:
                import traceback
                safe_print("详细错误信息:")
                safe_print(traceback.format_exc())
            return

        # 确保缓存目录存在
        try:
            os.makedirs(config.CACHE_DIR, exist_ok=True)
            if inputs.debug_mode:
                safe_print(f"✓ 缓存目录就绪: {config.CACHE_DIR}")
        except OSError as e:
            safe_print(f"无法创建缓存目录: {str(e)}")
            return

        # 处理清除缓存的选项
        if inputs.clear_cache:
            safe_print("正在清除所有缓存...")
            from src.core.cache_manager import clear_all_cache
            clear_all_cache()
            safe_print("缓存清除完成")

        # 设置全局配置
        config.set_debug_mode(inputs.debug_mode)
        config.set_api_cache(inputs.api_cache)
        config.set_group_cache(inputs.group_cache)


        folder_path = inputs.folder_path
        regex_str = inputs.regex_filter

        safe_print(f"处理目录: {folder_path}")

        # 获取所有目录名
        print_step(1, "收集文件夹信息")
        all_names = [name for name in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, name))]
        safe_print(f"找到 {len(all_names)} 个文件夹")
        
        # 目录名正则过滤
        if regex_str:
            safe_print(f"应用正则表达式: {regex_str}")
            try:
                pattern_filter = re.compile(regex_str)
                keywords_raw = [pattern_filter.sub("", name).strip() for name in all_names]
            except re.error as e:
                safe_print(f"正则表达式无效：{e}，将不过滤。")
                keywords_raw = [name.strip() for name in all_names]
        else:
            keywords_raw = [name.strip() for name in all_names]
        
        # 初始化标题匹配器，低于0.3不像人类了
        print_step(1.5, "执行模糊匹配")
        matched_keywords = []
        total = len(keywords_raw)

        if inputs.enable_fuzzy_match:

            # 所有模式都打印提示
            safe_print("正在加载模糊匹配模块...")
            from fuzz.fuzzy_match import TitleMatcher
            safe_print("模糊匹配模块加载完成")
            safe_print("初始化匹配器...")
            matcher = TitleMatcher(
                data_path=os.path.join("fuzz", "data", "vn_titles"),
                cache_dir=os.path.join("fuzz", "cache"),
                threshold=inputs.fuzzy_match_threshold
            )
            safe_print(f"\n开始匹配 {len(keywords_raw)} 个文件夹名称...")
            for idx, keyword in enumerate(keywords_raw, 1):
                safe_print(f"\r处理进度: {idx}/{total}", end="", flush=True)

                if not keyword:
                    matched_keywords.append("")
                    continue

                safe_print(f"\n正在匹配: {keyword}")
                results = matcher.match(keyword)

                if results:
                    matched_title = results[0].title
                    matched_score = results[0].score
                    matched_keywords.append(matched_title)
                    safe_print(f"✓ 匹配成功: {matched_title} (相似度: {matched_score:.2f})")

                    # 如果在debug模式下，显示更多匹配结果
                    if inputs.debug_mode and len(results) > 1:
                        safe_print("其他候选匹配:")
                        for r in results[1:4]:  # 显示前3个额外结果
                            safe_print(f"  - {r.title} (相似度: {r.score:.2f})")
                else:
                    matched_keywords.append(keyword)
                    safe_print(f"✗ 无匹配结果，保留原名: {keyword}")
        else:
            safe_print("模糊匹配已禁用，使用原始文件夹名")
            matched_keywords = keywords_raw

        safe_print("\n模糊匹配完成")
        
        # 使用匹配后的关键词
        keywords_raw = matched_keywords

        # 建立关键词到目录的映射
        keyword_to_dir = {}
        for name, keyword in zip(all_names, keywords_raw):
            safe_key = safe_folder_name(keyword)
            if not safe_key:
                continue
            keyword_to_dir.setdefault(safe_key, []).append(name)
        keywords = list(keyword_to_dir.keys())
        safe_print(f"提取了 {len(keywords)} 个关键词")
        
        # 异步查询VNDB API并处理结果
        print_step(2, "查询VNDB信息")
        requirement_types = inputs.get_requirement_types()
        result_dict = await process_vndb_queries_async(keywords, requirement_types)
        # 是否分组
        print_step(3, "文件夹分组")
        current_dir = folder_path
        if inputs.do_vn_group:
            safe_print("执行VisualNovel/NotMatched分组...")
            current_dir = divide_into_vn_groups(folder_path, keyword_to_dir, result_dict)
            safe_print("分组完成，继续下一步操作")
        else:
            safe_print("已跳过VisualNovel/NotMatched分组")

        # 提取有效字段
        VALID_FIELDS = extract_valid_fields(result_dict)
        # 标签分组
        print_step(4, "标签分组")
        if inputs.do_tag_grouping:
            # 使用别名转换
            field_path = inputs.tag_group_field
            # 自动替换为最相似标签
            if field_path and VALID_FIELDS:
                field_path = resolve_role_alias(field_path)
                if field_path and field_path not in VALID_FIELDS:
                    similar = get_most_similar_field(field_path, VALID_FIELDS)
                    if similar:
                        print(f"未找到完全匹配，自动替换为最相似标签: {similar}")
                        field_path = similar

            #if field_path:
                safe_print(f"使用标签 '{field_path}' 进行分组...")
                group_cache_key = f"group_{field_path}_{','.join(sorted(keywords))}"
                group_result = load_cache(group_cache_key) if config.ENABLE_GROUP_CACHE else None

                if group_result:
                    debug_print(f"命中分组缓存：{field_path}")
                else:
                    group_result = group_by_field(result_dict, field_path)

                    if config.ENABLE_GROUP_CACHE:
                        save_cache(group_cache_key, group_result)

                debug_print(f"按 {field_path} 分组结果：{json.dumps(group_result, ensure_ascii=False, indent=2)}")
                #print(group_result)
                # 执行分组
                current_dir = group_by_tag(current_dir, keyword_to_dir, result_dict, field_path, group_result)
        else:
            print("已跳过标签分组")

        # 规范化文件夹名称
        print_step(6, "规范化文件夹名称")
        if inputs.normalize_name:
            strict_mode = "严格模式" if inputs.normalize_strict else "保留原始格式"
            safe_print(f"执行规范化 ({strict_mode})...")
            recursive_rename(current_dir, keyword_to_dir, result_dict, inputs.normalize_strict)
            safe_print("规范化完成")
        else:
            safe_print("已跳过文件夹名称规范化")

        print_section("处理完成")

    finally:
        # 确保关闭异步会话
        await close_session()

async def process_vndb_queries_async(keywords, requirement_types=None):
    """
    异步处理VNDB查询并返回结果字典

    Args:
        keywords: 要查询的关键词列表
        requirement_types: API请求类型列表
    """
    if not keywords:
        return {}

    safe_print(f"\n开始批量查询 {len(keywords)} 个关键词...")

    # 使用异步批量查询
    json_data_dict = await fetch_vn_info_batch(keywords, requirement_types=requirement_types, max_concurrent=15)

    # 解析结果
    result_dict = {}
    for keyword, json_data in json_data_dict.items():
        parsed_data = parse_vn_response(json_data, requirement_types)
        if parsed_data:
            result_dict[keyword] = parsed_data
            debug_print(f"解析成功: {keyword}")
        else:
            result_dict[keyword] = None
            debug_print(f"未匹配到对象: {keyword}")

    safe_print(f"批量查询完成，成功匹配 {sum(1 for v in result_dict.values() if v)} 个关键词")
    return result_dict

def print_section(title):
    """打印分节标题"""
    width = 60
    safe_print("\n" + "=" * width)
    safe_print(title.center(width))
    safe_print("=" * width)

def print_step(step_num, title):
    """打印步骤标题"""
    safe_print(f"\n[步骤 {step_num}] {title}")


def main():
    """主程序入口函数，支持多通道输入"""
    from src.core.cli_parser import parse_args

    # 创建全局事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # 解析命令行参数 
        args = parse_args()

        # 根据参数决定使用哪种输入通道
        if args.get("config"):
            input_channel = ConfigFileChannel(args["config"])
        elif args.get("cli"):
            input_channel = CliChannel()
        elif args.get("api"):
            input_channel = ApiChannel()
        else:  # 默认或显式指定GUI
            input_channel = GuiChannel(loop=loop)
            # GUI模式支持多次使用
            while True:
                try:
                    user_inputs = input_channel.collect_inputs()
                    if not user_inputs.folder_path:
                        break
                    loop.run_until_complete(async_main(user_inputs))
                except Exception as e:
                    safe_print(f"任务执行出错: {str(e)}")
                    continue
            return 0

        # 非GUI模式执行一次
        user_inputs = input_channel.collect_inputs()
        loop.run_until_complete(async_main(user_inputs))
            
    except KeyboardInterrupt:
        safe_print("\n程序被用户中断")
        return 1
    except Exception as e:
        safe_print(f"错误: {str(e)}")
        return 1
    finally:
        try:
            loop.close()
        except Exception:
            pass
        
    return 0

if __name__ == "__main__":
    sys.exit(main())