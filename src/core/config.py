"""
配置文件，包含全局变量和配置选项
"""
import os
import appdirs

# 调试和缓存选项 - 这些会在运行时被main.py中的用户输入覆盖
DEBUG_MODE = False
ENABLE_API_CACHE = True
ENABLE_GROUP_CACHE = True


def set_debug_mode(val):
    global DEBUG_MODE
    DEBUG_MODE = val

def set_api_cache(val):
    global ENABLE_API_CACHE
    ENABLE_API_CACHE = val

def set_group_cache(val):
    global ENABLE_GROUP_CACHE
    ENABLE_GROUP_CACHE = val



# 缓存目录
APP_NAME = "VnGrouper"
CACHE_DIR = os.path.join(appdirs.user_cache_dir(APP_NAME), "global_cache")
os.makedirs(CACHE_DIR, exist_ok=True)