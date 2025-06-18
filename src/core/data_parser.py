"""
数据解析和处理模块
"""
import difflib
import re

from src.core.file_utils import debug_print

# 创建别名到原始角色名称的映射
role_aliases = {
    # 英文别名
    "artist": "staff.art",
    "character_designer": "staff.chardesign",
    "director": "staff.director",
    "editor": "staff.editor",
    "composer": "staff.music",
    "quality_assurance": "staff.qa",
    "scenario": "staff.scenario",
    "vocals": "staff.songs",
    "staff": "staff.staff",
    "translator": "staff.translator",
    "developers": "developers",
    "voice_actor": "staff.voice_actor",
    
    # 中文别名
    "开发者": "developers",
    "声优": "staff.voice_actor",
    "画师": "staff.art",
    "人物设计": "staff.chardesign",
    "剧本": "staff.scenario",
    "导演": "staff.director",
    "编辑": "staff.editor",
    "作曲": "staff.music",
    "质量保证": "staff.qa",
    "演唱": "staff.songs",
    "工作人员": "staff.staff",
    "翻译": "staff.translator",
}

def resolve_role_alias(role):
    """
    将角色别名转换回分组字段。

    Args:
        role (str): 需要转换的角色名称或别名
    Returns:
        str: 对应的分组字段，如果未找到匹配项则返回原角色
    """
    return role_aliases.get(role, role)

def clean_unicode_control_chars(data):
    """
    递归清除数据中的 Unicode 控制字符（如 \u200f, \u200e 等）。

    Args:
        data: 任意类型的输入数据 (str, list, dict, 等)
    Returns:
        清理后的数据
    """
    if isinstance(data, str):  # 如果是字符串，直接处理
        return re.sub(r'[\u200e\u200f\u202a-\u202e\u2060-\u206f]', '', data)
    elif isinstance(data, list):  # 如果是列表，递归处理每个元素
        return [clean_unicode_control_chars(item) for item in data]
    elif isinstance(data, dict):  # 如果是字典，递归处理每个键和值
        return {key: clean_unicode_control_chars(value) for key, value in data.items()}
    else:  # 其他类型（如 int, float, None 等）保持不变
        return data

def parse_vn_response(json_data, requirement_types=None):
    """
    解析VNDB API返回的视觉小说信息

    Args:
        json_data: API返回的JSON数据
        requirement_types: API请求类型列表，可能包含：
            1: 标题信息
            2: 开发者和工作人员信息
            3: 详细信息（原名和别名）

    Returns:
        dict: 解析后的数据对象
    """
    # 清理输入数据中的Unicode控制字符
    json_data = clean_unicode_control_chars(json_data)

    if not json_data or "results" not in json_data or not json_data["results"]:
        return None

    if not requirement_types:
        requirement_types = [1]  # 默认使用最基础的类型

    vn_data = json_data["results"][0]
    simple_obj = {}

    # 处理标题信息（始终包含）
    for title in vn_data.get("titles", []):
        if title.get("main"):
            simple_obj["title"] = title.get("title", "")
            break

    # 如果只需要标题信息，直接返回
    if max(requirement_types) == 1:
        return simple_obj

    # 处理开发者信息（type 2及以上）
    if 2 in requirement_types or 3 in requirement_types:
        developers = []
        for dev in vn_data.get("developers", []):
            dev_info = {"name": dev.get("name", "")}
            if 3 in requirement_types:  # 需要原名
                dev_info["original"] = dev.get("original", "")
            developers.append(dev_info)
        if developers:
            simple_obj["developers"] = developers

        # 处理Staff信息
        staff_dict = {}
        for staff in vn_data.get("staff", []):
            role = staff.get("role", "")
            if not role:
                continue

            staff_info = {"name": staff.get("name", "")}
            if 3 in requirement_types:  # 需要原名和别名
                staff_info.update({
                    "original": staff.get("original", ""),
                    "main_alias": ""
                })
                # 查找主要别名
                for alias in staff.get("aliases", []):
                    if alias.get("ismain"):
                        staff_info["main_alias"] = alias.get("name", "")
                        break

            staff_dict.setdefault(role, []).append(staff_info)

        # 处理声优信息
        va_list = []
        for va in vn_data.get("va", []):
            staff = va.get("staff", {})
            if not staff:
                continue

            va_info = {"name": staff.get("name", "")}
            if 3 in requirement_types:  # 需要原名和别名
                va_info.update({
                    "original": staff.get("original", ""),
                    "main_alias": ""
                })
                # 查找主要别名
                for alias in staff.get("aliases", []):
                    if alias.get("ismain"):
                        va_info["main_alias"] = alias.get("name", "")
                        break

            va_list.append(va_info)

        if va_list:
            staff_dict["voice_actor"] = va_list

        if staff_dict:
            simple_obj["staff"] = staff_dict

    return simple_obj
    
def get_by_path(obj, path):
    """
    根据路径获取对象中的值
    """
    parts = path.split('.')
    for part in parts:
        if isinstance(obj, dict):
            obj = obj.get(part, None)
        else:
            return None
    return obj

def extract_names(val):
    """
    从不同类型的值中提取名称列表
    """
    if isinstance(val, str):
        return [v.strip() for v in val.split(",") if v.strip()]
    elif isinstance(val, list):
        names = []
        for v in val:
            if isinstance(v, dict):
                name = v.get("name", "")
                if name:
                    names.append(name)
                # 如果有主要别名，也加入列表
                main_alias = v.get("main_alias", "")
                if main_alias:
                    names.append(main_alias)
        return names
    return []

def group_by_field(result_dict, field_path):
    """
    根据指定字段对结果进行分组
    """
    debug_print(f"\n开始根据指定字段对结果进行分组: {field_path}")
    group_dict = {}
    for keyword, obj in result_dict.items():
        if not obj:
            continue
        debug_print(f"正在处理关键词: {keyword}")
        val = get_by_path(obj, field_path)
        debug_print(f"获取到的原始值: {val}")
        names = extract_names(val)
        debug_print(f"提取的名称列表: {names}")
        if not names:
            continue
        merged_name = ",".join(sorted(set(names)))
        debug_print(f"合并后的分组名: {merged_name}")
        group_dict.setdefault(merged_name, []).append(keyword)
    debug_print(f"=== 最终分组结果 ===: {group_dict}\n")
    return group_dict

def extract_valid_fields(result_dict):
    """
    提取有效的分组字段
    """
    fields = set()
    for v in result_dict.values():
        if not v:
            continue
        # 顶层字段
        fields.update(v.keys())
        # staff 下的子字段
        if isinstance(v.get("staff"), dict):
            for staff_role in v["staff"].keys():
                fields.add(f"staff.{staff_role}")
    return sorted(fields)

def get_most_similar_field(user_input, valid_fields):
    """
    获取与用户输入最相似的字段
    """
    matches = difflib.get_close_matches(user_input, valid_fields, n=1, cutoff=0.3)
    return matches[0] if matches else None

def replace_unmatched_part(old_name: str, regex_str: str, keyword: str) -> str:
    """
    替换未匹配的部分
    """            
    import re
    result = ""
    last_end = 0
    for match in re.finditer(regex_str, old_name):
        start, end = match.span()
        if last_end < start:
            result += keyword  # 插入唯一未匹配部分
        result += old_name[start:end]
        last_end = end

    if last_end < len(old_name):
        result += keyword  # 未匹配部分在末尾

    return result if result else keyword  # 全不匹配的情况
