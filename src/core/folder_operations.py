"""
文件夹重命名和分组功能模块
"""
import os
from .file_utils import safe_folder_name, debug_print, move_folder
from .data_parser import replace_unmatched_part

def divide_into_vn_groups(folder_path, keyword_to_dir, result_dict):
    """
    将文件夹分为VisualNovel(VNDB查询得到)/NotMatched(查不到)两组
    """
    vn_dir = os.path.join(folder_path, "VisualNovel")
    novn_dir = os.path.join(folder_path, "NotMatched")
    os.makedirs(vn_dir, exist_ok=True)
    os.makedirs(novn_dir, exist_ok=True)

    for keyword in keyword_to_dir:
        for orig_dir in keyword_to_dir[keyword]:
            src_dir = os.path.join(folder_path, orig_dir)
            dst_name = safe_folder_name(orig_dir)

            if result_dict.get(keyword):
                dst_dir = os.path.join(vn_dir, dst_name)
            else:
                dst_dir = os.path.join(novn_dir, dst_name)

            move_folder(src_dir, dst_dir)

    print("已完成 VisualNovel/NotMatched 分组，等待下一步操作。")
    return vn_dir

def group_by_tag(current_dir, keyword_to_dir, result_dict, field_path, group_result):
    """
    根据标签对文件夹进行分组
    """
    # Windows文件名长度限制
    MAX_PATH_LENGTH = 240  # 留一些余量，实际限制是255
    MANY_PEOPLE_GROUP = "人员过多"

    debug_print(f"\n=== 开始标签分组 ===: {field_path}")
    debug_print(f"加载分组结果: {group_result}")

    other_dir = os.path.join(current_dir, "_other")
    many_people_dir = os.path.join(current_dir, MANY_PEOPLE_GROUP)
    os.makedirs(other_dir, exist_ok=True)
    os.makedirs(many_people_dir, exist_ok=True)

    # 创建反向映射：文件夹名到其分组的映射
    folder_to_group = {}
    for group_name, keywords in group_result.items():
        for keyword in keywords:
            if keyword in keyword_to_dir:
                for folder in keyword_to_dir[keyword]:
                    folder_to_group[safe_folder_name(folder)] = group_name

    # 处理所有文件夹
    for keyword, folders in keyword_to_dir.items():
        if not result_dict.get(keyword):
            continue
            
        for folder in folders:
            safe_folder = safe_folder_name(folder)
            group_name = folder_to_group.get(safe_folder)
            
            if group_name:
                # 检查分组名长度
                safe_group_name = safe_folder_name(group_name)
                if len(safe_group_name) > MAX_PATH_LENGTH:
                    # 如果分组名过长，移动到"人员过多"分组
                    debug_print(f"分组名过长({len(safe_group_name)} 个字符), 移动至 {MANY_PEOPLE_GROUP}: {safe_folder}")
                    dst = os.path.join(many_people_dir, safe_folder)
                else:
                    # 创建分组目录
                    group_dir = os.path.join(current_dir, safe_group_name)
                    try:
                        os.makedirs(group_dir, exist_ok=True)
                        debug_print(f"创建了分组文件夹: {group_dir}")
                        dst = os.path.join(group_dir, safe_folder)
                    except Exception as e:
                        debug_print(f"创建分组文件夹失败: {group_dir}, error: {e}")
                        # 如果创建分组目录失败，移动到"人员过多"分组
                        debug_print(f"移动至 {MANY_PEOPLE_GROUP} ，这是报错信息: {safe_folder}")
                        dst = os.path.join(many_people_dir, safe_folder)

                # 移动文件夹
                src = os.path.join(current_dir, safe_folder)
                if os.path.exists(src):
                    move_folder(src, dst)
            else:
                # 移动到_other目录
                src = os.path.join(current_dir, safe_folder)
                dst = os.path.join(other_dir, safe_folder)
                if os.path.exists(src):
                    debug_print(f"移动到其它目录: {safe_folder}")
                    move_folder(src, dst)

    debug_print("分组完成，将分组文件夹名称替换为原名\n")
    return normalize_group_names(current_dir, group_result, result_dict, field_path)

def normalize_group_names(current_dir, group_result, result_dict, field_path):
    """
    将分组文件夹名替换为原名
    """
    tag_parts = field_path.split('.')
    tag_type = tag_parts[0]
    is_staff = tag_type == "staff"

    for merged_group_name, keyword_list in group_result.items():
        original_names = set()

        for keyword in keyword_list:
            obj = result_dict.get(keyword)
            if not obj:
                continue

            if is_staff and len(tag_parts) > 1:
                role = tag_parts[1]
                staff_list = obj.get("staff", {}).get(role, [])
                for staff in staff_list:
                    if staff.get("name") in merged_group_name:
                        # 优先使用原名，其次使用主要别名
                        name = staff.get("original", "") or staff.get("main_alias", "") or staff.get("name", "")
                        if name:
                            original_names.add(name)
            else:  # developers
                devs = obj.get("developers", [])
                for dev in devs:
                    if dev.get("name") in merged_group_name:
                        # 优先使用原名，其次使用英文名
                        name = dev.get("original", "") or dev.get("name", "")
                        if name:
                            original_names.add(name)

        if not original_names:
            debug_print(f"未找到任何原名: {merged_group_name}")
            continue

        # 执行重命名
        new_merged_name = ",".join(sorted(original_names))
        old_folder = os.path.join(current_dir, safe_folder_name(merged_group_name))
        new_folder = os.path.join(current_dir, safe_folder_name(new_merged_name))
        
        if old_folder != new_folder:
            try:
                os.rename(old_folder, new_folder)
                debug_print(f"重命名成功: {old_folder} -> {new_folder}")
            except Exception as e:
                debug_print(f"重命名失败: {old_folder} -> {new_folder}, 原因: {e}")

    return current_dir

def recursive_rename(current_dir, keyword_to_dir, result_dict, strict_mode=False, regex_str=""):
    """
    递归重命名文件夹，将名称规范化为通用名称
    
    Args:
        current_dir: 当前处理的目录
        keyword_to_dir: 关键词到目录的映射
        result_dict: API查询结果字典
        strict_mode: 是否使用严格模式（仅保留通用名）
    """
    for item in os.listdir(current_dir):
        item_path = os.path.join(current_dir, item)
        if not os.path.isdir(item_path):
            continue

        # 如果是子目录，递归处理
        recursive_rename(item_path, keyword_to_dir, result_dict, strict_mode=strict_mode, regex_str=regex_str)

        # 查找对应的关键词
        safe_name = safe_folder_name(item)
        found_keyword = None
        for keyword, dirs in keyword_to_dir.items():
            if any(safe_folder_name(d) == safe_name for d in dirs):
                found_keyword = keyword
                break

        if not found_keyword:
            continue

        # 获取API结果
        vn_data = result_dict.get(found_keyword)
        if not vn_data:
            continue

        # 获取标准名称
        title = vn_data.get("title", "")
        if not title:
            continue

        # 构建新名称
        if strict_mode:
            # 严格模式：将原目录名替换为通用名
            new_name = safe_folder_name(title)
        else:
            # 保留原始格式：用正则分割原目录名，保留匹配的部分，将非匹配部分替换为通用名后重组两部分
            if title.lower() not in item.lower():
                new_name = replace_unmatched_part(item,regex_str,title)
            else:
                new_name = item

        # 执行重命名
        if new_name and new_name != item:
            old_path = item_path
            new_path = os.path.join(current_dir, new_name)
            try:
                os.rename(old_path, new_path)
                debug_print(f"重命名: {old_path} -> {new_path}")
            except Exception as e:
                debug_print(f"重命名失败: {old_path} -> {new_path}, 原因: {e}")