"""
缓存管理模块
"""
import os
import json
import hashlib
import src.core.config as config

def generate_cache_path(key):
    """
    根据缓存键生成缓存文件路径
    """
    h = hashlib.md5(key.encode("utf-8")).hexdigest()
    return os.path.join(config.CACHE_DIR, f"{h}.json")

def save_cache(key, data):
    """
    保存数据到缓存
    """
    # 确保缓存目录存在
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    
    # 使用配置中的CACHE_DIR
    cache_path = generate_cache_path(key)
    
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_cache(key):
    """
    从缓存加载数据
    """
    # 使用配置中的CACHE_DIR
    cache_path = generate_cache_path(key)
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def clear_all_cache():
    """
    清除所有缓存文件
    """
    import os
    import shutil
    import src.core.config as config
    
    if os.path.exists(config.CACHE_DIR):
        shutil.rmtree(config.CACHE_DIR)
        os.makedirs(config.CACHE_DIR, exist_ok=True)