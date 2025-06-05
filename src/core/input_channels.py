"""
输入通道接口实现，支持多种输入方式
"""
import os
import json
import configparser
from abc import ABC, abstractmethod
from typing import Dict, Any
from src.core.models import UserInputs
from src.core.data_parser import role_aliases

class InputChannel(ABC):
    """输入通道抽象基类"""
    
    @abstractmethod
    def collect_inputs(self) -> UserInputs:
        """收集用户输入并返回UserInputs对象"""
        pass
    
    @staticmethod
    def validate_inputs(inputs_dict: Dict[str, Any]) -> UserInputs:
        """验证输入并转换为UserInputs对象"""
        try:
            # 设置默认值
            inputs_dict.setdefault("regex_filter", "")
            inputs_dict.setdefault("folder_path", "")
            inputs_dict.setdefault("enable_fuzzy_match", False)
            inputs_dict.setdefault("fuzzy_match_threshold", 0.8)
            
            # 确保布尔值字段不为None
            bool_fields = [
                "debug_mode", "api_cache", "group_cache",
                "do_vn_group", "do_tag_grouping", "rename_to_original",
                "normalize_name", "normalize_strict", "enable_fuzzy_match"
            ]
            for field in bool_fields:
                inputs_dict[field] = bool(inputs_dict.get(field, False))
            
            # 条件默认值
            if not inputs_dict["do_tag_grouping"]:
                inputs_dict["tag_group_field"] = ""
                inputs_dict["rename_to_original"] = False
            if not inputs_dict["normalize_name"]:
                inputs_dict["normalize_strict"] = False
                
            # 使用Pydantic模型验证输入
            return UserInputs(**inputs_dict)
        except Exception as e:
            raise ValueError(f"输入验证失败: {e}")


class CliChannel(InputChannel):
    """命令行输入通道"""
    
    def collect_inputs(self) -> UserInputs:
        """通过命令行交互收集用户输入"""
        inputs_dict = {}
        
        # 基础配置
        inputs_dict["debug_mode"] = self._ask_yn("是否开启调试模式？", False)
        inputs_dict["regex_filter"] = input("请输入用于过滤目录名的正则表达式（留空则不过滤）：").strip()
        
        # 缓存设置
        inputs_dict["clear_cache"] = self._ask_yn("是否清除所有缓存？", False)
        inputs_dict["api_cache"] = self._ask_yn("是否启用API查询缓存？", True)
        inputs_dict["group_cache"] = self._ask_yn("是否启用分组结果缓存？", True) 

        
        # 文件夹路径
        folder_path = input("请输入待处理的文件夹路径：").strip()
        if not folder_path:
            raise ValueError("文件夹路径不能为空")
        if not os.path.isdir(folder_path):
            raise ValueError(f"指定的路径不是有效目录: {folder_path}")
        inputs_dict["folder_path"] = folder_path
        
        # 分组设置
        inputs_dict["do_vn_group"] = self._ask_yn("是否将文件夹分为VisualNovel/NotMatched两组？", True)
        inputs_dict["do_tag_grouping"] = self._ask_yn("是否进行标签分组？", True)
        
        if inputs_dict["do_tag_grouping"]:
            # 展示英文标签提示
            eng_aliases = [k for k in role_aliases.keys() if not any('\u4e00' <= c <= '\u9fff' for c in k)]
            print("\n可用的分组字段：")
            for alias in sorted(eng_aliases):
                print(f"  {alias}")
            print()
            inputs_dict["tag_group_field"] = input("请输入要分组的标签（如 developers 或 scenario）：").strip()
            
            if inputs_dict["tag_group_field"]:
                inputs_dict["rename_to_original"] = self._ask_yn("是否将分组文件夹名替换为原名？", False)
        
        # 命名规范
        inputs_dict["normalize_name"] = self._ask_yn("是否将galgame文件夹名称规范化为通用名称？", False)
        if inputs_dict["normalize_name"]:
            inputs_dict["normalize_strict"] = self._ask_yn("是否严格规范化（仅保留通用名）？", False)
            
        # 模糊匹配设置
        inputs_dict["enable_fuzzy_match"] = self._ask_yn("是否启用模糊匹配？", False)
        if inputs_dict["enable_fuzzy_match"]:
            inputs_dict["fuzzy_match_threshold"] = input("请输入模糊匹配阈值(0.0-1.0，默认0.4)：").strip() or "0.4"
        
        # 验证并返回
        return self.validate_inputs(inputs_dict)
    
    def _ask_yn(self, prompt: str, default: bool = False) -> bool:
        """获取用户是/否输入"""
        default_str = 'y' if default else 'n'
        while True:
            val = input(f"{prompt} (y/n，默认{default_str}): ").strip().lower()
            if not val:
                return default
            if val in ('y', 'yes'):
                return True
            if val in ('n', 'no'):
                return False
            print("请输入 y 或 n")

class ConfigFileChannel(InputChannel):
    """配置文件输入通道"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
    
    def collect_inputs(self) -> UserInputs:
        """从配置文件读取用户输入"""
        inputs_dict = {
            "debug_mode": False,
            "regex_filter": "",
            "clear_cache": False,
            "api_cache": True,
            "group_cache": True,
            "folder_path": "",
            "do_vn_group": True,
            "do_tag_grouping": False,
            "tag_group_field": "",
            "rename_to_original": False,
            "normalize_name": False,
            "normalize_strict": False,
            "enable_fuzzy_match": False,
            "fuzzy_match_threshold": 0.8
        }
        
        # 判断文件类型
        if self.config_path.endswith('.json'):
            # 读取JSON配置
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    inputs_dict = json.load(f)
                    print(f"DEBUG: 读取到的配置: {inputs_dict}")  # 添加调试输出
                    print(f"DEBUG: regex_filter 类型: {type(inputs_dict.get('regex_filter'))}")  # 检查类型
            except Exception as e:
                raise ValueError(f"JSON配置文件读取失败: {e}")
                
        elif self.config_path.endswith('.ini') or self.config_path.endswith('.conf'):
            # 读取INI配置
            try:
                config = configparser.ConfigParser()
                config.read(self.config_path, encoding='utf-8')
                
                if 'UserInputs' in config:
                    for key, value in config['UserInputs'].items():
                        # 转换布尔值
                        if value.lower() in ('true', 'yes', 'y', '1'):
                            inputs_dict[key] = True
                        elif value.lower() in ('false', 'no', 'n', '0'):
                            inputs_dict[key] = False
                        else:
                            inputs_dict[key] = value
            except Exception as e:
                raise ValueError(f"INI配置文件读取失败: {e}")
        else:
            raise ValueError(f"不支持的配置文件格式: {self.config_path}")
        
        # 确保folder_path至少是空字符串
        if 'folder_path' in inputs_dict and inputs_dict['folder_path'] is None:
            inputs_dict['folder_path'] = ""
        
        # 确保regex_filter不为None
        if inputs_dict.get('regex_filter') is None:
            print("DEBUG: regex_filter 为 None，设置为空字符串")
            inputs_dict['regex_filter'] = ""

        # 验证并返回
        return self.validate_inputs(inputs_dict)

# gui，已迁移至gui模块
# class GuiChannel(InputChannel):
#     """图形界面输入通道"""

#     def collect_inputs(self) -> UserInputs:
#         """通过GUI收集用户输入"""
#         root = tk.Tk()
#         root.title("VNDB处理工具 - 输入参数")
#         root.geometry("600x700")

#         # 使用字典存储所有变量
#         inputs_dict = {
#             "debug_mode": tk.BooleanVar(value=False),
#             "regex_filter": tk.StringVar(value=""),
#             "api_cache": tk.BooleanVar(value=True),
#             "group_cache": tk.BooleanVar(value=True),
#             
#             "folder_path": tk.StringVar(value=""),
#             "do_vn_group": tk.BooleanVar(value=True),
#             "do_tag_grouping": tk.BooleanVar(value=False),
#             "tag_group_field": tk.StringVar(value=""),
#             "rename_to_original": tk.BooleanVar(value=False),
#             "normalize_name": tk.BooleanVar(value=False),
#             "normalize_strict": tk.BooleanVar(value=False)
#         }

#         # 创建主框架并设置滚动条
#         canvas = tk.Canvas(root)
#         scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
#         main_frame = tk.Frame(canvas)

#         # 配置滚动
#         canvas.configure(yscrollcommand=scrollbar.set)
#         scrollbar.pack(side="right", fill="y")
#         canvas.pack(side="left", fill="both", expand=True)
#         canvas.create_window((0, 0), window=main_frame, anchor="nw")
#         main_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

#         # 文件夹选择
#         folder_frame = tk.LabelFrame(main_frame, text="文件夹选择", padx=10, pady=5)
#         folder_frame.pack(fill=tk.X, padx=10, pady=5)
        
#         folder_entry = tk.Entry(folder_frame, textvariable=inputs_dict["folder_path"])
#         folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
#         def select_folder():
#             folder = filedialog.askdirectory()
#             if folder:
#                 inputs_dict["folder_path"].set(folder)
        
#         tk.Button(folder_frame, text="选择文件夹", command=select_folder).pack(side=tk.RIGHT)

#         # 基础设置
#         basic_frame = tk.LabelFrame(main_frame, text="基础设置", padx=10, pady=5)
#         basic_frame.pack(fill=tk.X, padx=10, pady=5)
#         tk.Checkbutton(basic_frame, text="调试模式", variable=inputs_dict["debug_mode"]).pack(anchor=tk.W)
#         tk.Label(basic_frame, text="正则过滤:").pack(anchor=tk.W)
#         tk.Entry(basic_frame, textvariable=inputs_dict["regex_filter"]).pack(fill=tk.X)

#         # 缓存设置
#         cache_frame = tk.LabelFrame(main_frame, text="缓存设置", padx=10, pady=5)
#         cache_frame.pack(fill=tk.X, padx=10, pady=5)
#         tk.Checkbutton(cache_frame, text="API缓存", variable=inputs_dict["api_cache"]).pack(anchor=tk.W)
#         tk.Checkbutton(cache_frame, text="分组缓存", variable=inputs_dict["group_cache"]).pack(anchor=tk.W)
#         

#         # 分组设置
#         group_frame = tk.LabelFrame(main_frame, text="分组设置", padx=10, pady=5)
#         group_frame.pack(fill=tk.X, padx=10, pady=5)
#         tk.Checkbutton(group_frame, text="VN/NotMatched分组", variable=inputs_dict["do_vn_group"]).pack(anchor=tk.W)
        
#         def update_tag_group_state():
#             state = "normal" if inputs_dict["do_tag_grouping"].get() else "disabled"
#             tag_field_entry.configure(state=state)
#             rename_button.configure(state=state)
        
#         tk.Checkbutton(group_frame, text="标签分组", variable=inputs_dict["do_tag_grouping"], 
#                       command=update_tag_group_state).pack(anchor=tk.W)
#         tk.Label(group_frame, text="标签字段:").pack(anchor=tk.W)
#         tag_field_entry = tk.Entry(group_frame, textvariable=inputs_dict["tag_group_field"])
#         tag_field_entry.pack(fill=tk.X)
#         rename_button = tk.Checkbutton(group_frame, text="使用原名重命名", 
#                                      variable=inputs_dict["rename_to_original"])
#         rename_button.pack(anchor=tk.W)

#         # 命名规范
#         name_frame = tk.LabelFrame(main_frame, text="命名规范", padx=10, pady=5)
#         name_frame.pack(fill=tk.X, padx=10, pady=5)
        
#         def update_normalize_state():
#             state = "normal" if inputs_dict["normalize_name"].get() else "disabled"
#             strict_button.configure(state=state)
        
#         tk.Checkbutton(name_frame, text="规范化名称", variable=inputs_dict["normalize_name"],
#                       command=update_normalize_state).pack(anchor=tk.W)
#         strict_button = tk.Checkbutton(name_frame, text="严格规范化", 
#                                      variable=inputs_dict["normalize_strict"])
#         strict_button.pack(anchor=tk.W)

#         # 初始化状态
#         update_tag_group_state()
#         update_normalize_state()

#         # 结果变量
#         result = {"confirmed": False, "values": {}}

#         def on_confirm():
#             # 验证文件夹路径
#             if not inputs_dict["folder_path"].get().strip():
#                 messagebox.showerror("错误", "请选择要处理的文件夹")
#                 return
            
#             # 收集所有输入
#             result["values"] = {
#                 "debug_mode": inputs_dict["debug_mode"].get(),
#                 "regex_filter": inputs_dict["regex_filter"].get(),
#                 "api_cache": inputs_dict["api_cache"].get(),
#                 "group_cache": inputs_dict["group_cache"].get(),
#                 
#                 "folder_path": inputs_dict["folder_path"].get(),
#                 "do_vn_group": inputs_dict["do_vn_group"].get(),
#                 "do_tag_grouping": inputs_dict["do_tag_grouping"].get(),
#                 "tag_group_field": inputs_dict["tag_group_field"].get(),
#                 "rename_to_original": inputs_dict["rename_to_original"].get(),
#                 "normalize_name": inputs_dict["normalize_name"].get(),
#                 "normalize_strict": inputs_dict["normalize_strict"].get()
#             }
#             result["confirmed"] = True
#             root.destroy()

#         def on_cancel():
#             root.destroy()

#         # 按钮框架
#         button_frame = tk.Frame(main_frame)
#         button_frame.pack(fill=tk.X, padx=10, pady=20)
#         tk.Button(button_frame, text="取消", command=on_cancel, width=10).pack(side=tk.RIGHT, padx=5)
#         tk.Button(button_frame, text="确定", command=on_confirm, width=10).pack(side=tk.RIGHT, padx=5)

#         # 运行GUI
#         root.mainloop()

#         # 检查结果
#         if not result.get("confirmed"):
#             raise ValueError("用户取消了操作")

#         # 验证并返回
#         return self.validate_inputs(result["values"])

class ApiChannel(InputChannel):
    """API调用输入通道"""
    
    def __init__(self, api_data: Dict[str, Any]):
        self.api_data = api_data
    
    def collect_inputs(self) -> UserInputs:
        """从API数据构建用户输入"""
        # 直接验证API提供的数据
        return self.validate_inputs(self.api_data)