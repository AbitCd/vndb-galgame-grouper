"""
文件和文件夹处理相关的实用函数
"""
import os
import re
import shutil
import src.core.config as config

def safe_print(*args, **kwargs):
    """安全的打印函数，处理无控制台情况"""
    try:
        print(*args, **kwargs)
    except AttributeError:
        # 如果stdout为None，忽略flush操作
        if 'flush' in kwargs:
            del kwargs['flush']
        try:
            print(*args, **kwargs)
        except (AttributeError, IOError):
            pass
def safe_folder_name(name):
    """
    将文件夹名称转换为安全的格式
    """
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)  # 合并多余空格
    name = re.sub(r'[<>:"/\\|?*]', '_', name)  # 替换非法字符
    name = re.sub(r'[\x00-\x1f]', '_', name)  # 替换控制字符
    return name if name else "_empty"

def debug_print(*args, **kwargs):
    """
    调试模式下的打印函数
    """
    if config.DEBUG_MODE:
        print(*args, **kwargs)

def move_folder(src, dst):
    """
    安全地移动文件夹，处理异常情况
    """
    try:
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.move(src, dst)
            debug_print(f"已移动: {src} -> {dst}")
            return True
        elif os.path.exists(dst):
            debug_print(f"目标文件夹已存在: {dst}")
        elif not os.path.exists(src):
            debug_print(f"源文件夹不存在: {src}")
        return False
    except Exception as e:
        debug_print(f"移动目录出错: {src} -> {dst}，原因: {e}")
        return False