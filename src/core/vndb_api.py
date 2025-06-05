"""
VNDB API 请求管理模块，包含所有与VNDB相关的API调用（异步版本）
"""
import asyncio
import aiohttp
import src.core.config as config
from .cache_manager import load_cache, save_cache
from .file_utils import debug_print

# 全局会话对象，避免重复创建
_session = None

async def get_session():
    """获取全局异步HTTP会话"""
    global _session
    if _session is None or _session.closed:
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(ssl=False)
        _session = aiohttp.ClientSession(timeout=timeout, connector=connector)
    return _session

async def close_session():
    """关闭异步会话并清理资源"""
    global _session
    if _session:
        await _session.close()
        _session = None
    await asyncio.sleep(0.5)

async def fetch_vn_info_async(keyword, requirement_types=3):
    """
    异步查询视觉小说信息

    Args:
        keyword: 搜索关键词
        requirement_type: 需求类型
            1: 仅标题信息 (用于名称规范化/严格规范化/文件夹分组)
            2: 开发者和工作人员信息 (标签分组但不替换文件夹名)
            3: 详细信息 (标签分组并替换文件夹名)

    Returns:
        dict: API响应数据
    """
    url = "https://api.vndb.org/kana/vn"
    headers = {"Content-Type": "application/json"}

    # 根据需求类型组合设置API请求字段
    fields = "titles{title,main}"  # 基础字段总是需要的
    
    # 如果需要开发者和工作人员信息 (type 2)
    if 2 in requirement_types:
        fields += ", developers{name}, staff{name,role}, va.staff{name}"
    
    # 如果需要详细信息 (type 3)，升级之前的字段定义
    if 3 in requirement_types:
        if "developers{name}" in fields:
            fields = fields.replace("developers{name}", "developers{original,name}")
        else:
            fields += ", developers{original,name}"
            
        if "staff{name,role}" in fields:
            fields = fields.replace("staff{name,role}", "staff{original,name,role,aliases{name,ismain}}")
        else:
            fields += ", staff{original,name,role,aliases{name,ismain}}"
            
        if "va.staff{name}" in fields:
            fields = fields.replace("va.staff{name}", "va.staff{original,name,aliases{name,ismain}}")
        else:
            fields += ", va.staff{original,name,aliases{name,ismain}}"

    data = {
        "filters": ["search", "=", keyword],
        "fields": fields
    }

    try:
        session = await get_session()
        async with session.post(url, headers=headers, json=data) as response:
            response.raise_for_status()
            return await response.json()
    except Exception as e:
        debug_print(f"请求或解析失败: {keyword}, 原因: {e}")
        return None

async def fetch_vn_info_batch(keywords, requirement_types=None, max_concurrent=15):
    """
    批量获取VN信息

    Args:
        keywords: 要查询的关键词列表
        requirement_types: API请求类型列表
        max_concurrent: 最大并发请求数
    """
    if not keywords:
        return {}

    # 创建信号量控制并发
    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = []

    # 创建所有查询任务
    for keyword in keywords:
        task = fetch_vn_info_with_cache(keyword, requirement_types, semaphore)
        tasks.append(task)

    # 等待所有任务完成
    results = await asyncio.gather(*tasks)

    # 将结果组织成字典
    return dict(zip(keywords, results))

async def fetch_vn_info_with_cache(keyword, requirement_types, semaphore):
    """使用缓存获取VN信息"""
    if not requirement_types:
        requirement_types = [1]  # 默认使用最基础的请求类型
    
    # 生成包含requirement_types信息的缓存键
    types_str = "_".join(map(str, sorted(requirement_types)))
    cache_key = f"vndb_{keyword}_{types_str}"
    
    if config.ENABLE_API_CACHE:
        cached = load_cache(cache_key)
        if cached:
            debug_print(f"命中API缓存：{keyword} (types: {types_str})")
            return cached

    async with semaphore:
        try:
            result = await fetch_vn_info_async(keyword, requirement_types)
            if config.ENABLE_API_CACHE and result:
                save_cache(cache_key, result)
                debug_print(f"缓存API结果：{keyword} (types: {types_str})")
            return result
        except Exception as e:
            debug_print(f"查询出错 {keyword}: {e}")
            return None