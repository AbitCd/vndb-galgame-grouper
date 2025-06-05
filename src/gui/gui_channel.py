import tkinter as tk
from tkinter import filedialog, messagebox
from src.core.input_channels import InputChannel
from src.core.models import UserInputs
from tkinter import ttk
from src.core.data_parser import role_aliases
import asyncio
import sys
class VndbInputView:
    """VNDB输入界面视图类"""
    
    def __init__(self, root=None, loop=None):
        self.root = root or tk.Tk()
        self.loop = loop or asyncio.get_event_loop()
        self.root.title("VNDB自动分类重命名工具")
        self.root.geometry("780x560")
        # 计算窗口居中位置
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 780) // 2
        y = (screen_height - 560) // 2
        self.root.geometry(f"+{x}+{y}")
        
        # 回调函数
        self.on_confirm_callback = None
        self.on_cancel_callback = None
        
        # 输入变量
        self.inputs_dict = {
            "debug_mode": tk.BooleanVar(value=False),
            "regex_filter": tk.StringVar(value=""),
            "clear_cache": tk.BooleanVar(value=False),
            "api_cache": tk.BooleanVar(value=True),
            "group_cache": tk.BooleanVar(value=True),
            "folder_path": tk.StringVar(value=""),
            "do_vn_group": tk.BooleanVar(value=True),
            "do_tag_grouping": tk.BooleanVar(value=False),
            "tag_group_field": tk.StringVar(value=""),
            "rename_to_original": tk.BooleanVar(value=False),
            "normalize_name": tk.BooleanVar(value=False),
            "normalize_strict": tk.BooleanVar(value=False),
            "enable_fuzzy_match": tk.BooleanVar(value=False),
            "fuzzy_match_threshold": tk.StringVar(value="0.4")
        }
        
        # GUI组件引用
        self.tag_field_entry = None
        self.rename_button = None
        self.strict_button = None
        self.fuzzy_threshold_entry = None
        
        # 创建UI组件
        self._create_ui()
    
    def _create_ui(self):
        # 创建主框架并设置滚动条
        canvas = tk.Canvas(self.root)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        main_frame = tk.Frame(canvas)

        # 配置滚动
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        main_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # 创建左右两个主框架
        left_frame = tk.Frame(main_frame)
        right_frame = tk.Frame(main_frame)
        
        main_frame.grid_columnconfigure(0, weight=5)  # 左侧占比50%
        main_frame.grid_columnconfigure(1, weight=5)  # 右侧占比50%
        
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=3)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=3)

        # 左侧框架内容
        # 文件夹选择
        folder_frame = tk.LabelFrame(left_frame, text="文件夹选择", padx=10, pady=5)
        folder_frame.pack(fill=tk.X, expand=True, padx=5, pady=3)
        
        folder_entry = tk.Entry(folder_frame, textvariable=self.inputs_dict["folder_path"], width=50)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,3))
        
        def select_folder():
            folder = filedialog.askdirectory()
            if folder:
                self.inputs_dict["folder_path"].set(folder)
        
        tk.Button(folder_frame, text="选择文件夹", command=select_folder).pack(side=tk.RIGHT, padx=(3,5))

        # 基础设置
        basic_frame = tk.LabelFrame(left_frame, text="基础设置", padx=10, pady=5)
        basic_frame.pack(fill=tk.X, expand=True, padx=5, pady=3)
        tk.Checkbutton(basic_frame, text="调试模式", variable=self.inputs_dict["debug_mode"]).pack(anchor=tk.W, pady=(0,5))
        tk.Label(basic_frame, text="正则过滤:").pack(anchor=tk.W, pady=(0,2))
        tk.Entry(basic_frame, textvariable=self.inputs_dict["regex_filter"], width=40).pack(fill=tk.X, pady=(0,5))
        
        # 缓存设置
        cache_frame = tk.LabelFrame(left_frame, text="缓存设置", padx=10, pady=5)
        cache_frame.pack(fill=tk.X, expand=True, padx=5, pady=3)
        
        def clear_cache_confirm():
            if messagebox.askyesno("确认", "确定要清除所有缓存吗？\n此操作不可撤销。"):
                try:
                    self.clear_cache()
                    messagebox.showinfo("成功", "所有缓存已清除")
                except Exception as e:
                    messagebox.showerror("错误", f"清除缓存时出错：{str(e)}")
        
        tk.Button(cache_frame, text="清除所有缓存", command=clear_cache_confirm).pack(anchor=tk.W, pady=(2,8))
        cache_check_frame = tk.Frame(cache_frame)
        cache_check_frame.pack(fill=tk.X)
        tk.Checkbutton(cache_check_frame, text="API缓存", variable=self.inputs_dict["api_cache"]).pack(side=tk.LEFT, padx=(0,20))
        tk.Checkbutton(cache_check_frame, text="分组缓存", variable=self.inputs_dict["group_cache"]).pack(side=tk.LEFT)
        
        # 模糊匹配设置
        fuzzy_frame = tk.Frame(basic_frame)
        fuzzy_frame.pack(fill=tk.X, pady=5)
        fuzzy_check = tk.Checkbutton(fuzzy_frame, text="启用模糊匹配", 
                                   variable=self.inputs_dict["enable_fuzzy_match"],
                                   command=lambda: self.fuzzy_threshold_entry.configure(
                                       state="normal" if self.inputs_dict["enable_fuzzy_match"].get() else "disabled"))
        fuzzy_check.pack(side=tk.LEFT)
        
        tk.Label(fuzzy_frame, text="阈值(0-1，越高越严格，0.3以下会乱匹配):").pack(side=tk.LEFT, padx=(15,3))
        self.fuzzy_threshold_entry = tk.Entry(fuzzy_frame, textvariable=self.inputs_dict["fuzzy_match_threshold"], width=8)
        self.fuzzy_threshold_entry.pack(side=tk.LEFT)
        self.fuzzy_threshold_entry.configure(state="disabled")  # 初始状态设为禁用

        # 右侧框架内容
        # 分组设置
        group_frame = tk.LabelFrame(right_frame, text="分组设置", padx=10, pady=5)
        group_frame.pack(fill=tk.X, expand=True, padx=5, pady=3)
        tk.Checkbutton(group_frame, text="VN/NotMatched分组", variable=self.inputs_dict["do_vn_group"]).pack(anchor=tk.W)
        
        def update_tag_group_state():
            state = "normal" if self.inputs_dict["do_tag_grouping"].get() else "disabled"
            self.tag_field_entry.configure(state=state)
            self.rename_button.configure(state=state)
        
        tk.Checkbutton(group_frame, text="标签分组", variable=self.inputs_dict["do_tag_grouping"], 
                    command=update_tag_group_state).pack(anchor=tk.W)
        tk.Label(group_frame, text="标签字段:").pack(anchor=tk.W)
        # 获取所有中文别名
        chinese_aliases = [k for k in role_aliases.keys() if any('\u4e00' <= c <= '\u9fff' for c in k)]
        self.tag_field_entry = ttk.Combobox(group_frame, textvariable=self.inputs_dict["tag_group_field"], 
                                          values=chinese_aliases, state="readonly", width=30)
        self.tag_field_entry.pack(fill=tk.X, pady=(2,5))
        self.rename_button = tk.Checkbutton(group_frame, text="标签分组文件夹使用原名", 
                                    variable=self.inputs_dict["rename_to_original"])
        self.rename_button.pack(anchor=tk.W, pady=(0,3))

        # 命名规范
        name_frame = tk.LabelFrame(right_frame, text="命名规范", padx=10, pady=5)
        name_frame.pack(fill=tk.X, expand=True, padx=5, pady=3)
        
        def update_normalize_state():
            state = "normal" if self.inputs_dict["normalize_name"].get() else "disabled"
            self.strict_button.configure(state=state)
        
        tk.Checkbutton(name_frame, text="使用VNDB的规范化名称", variable=self.inputs_dict["normalize_name"],
                    command=update_normalize_state).pack(anchor=tk.W)
        self.strict_button = tk.Checkbutton(name_frame, text="使用正则过滤的严格规范化", 
                                    variable=self.inputs_dict["normalize_strict"])
        self.strict_button.pack(anchor=tk.W)

        # 创建日志显示区域
        log_frame = tk.LabelFrame(main_frame, text="处理日志", padx=5, pady=3)
        log_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=3)
        log_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # 创建文本框和滚动条
        self.log_text = tk.Text(log_frame, height=10, width=80, wrap=tk.WORD)
        scrollbar = tk.Scrollbar(log_frame)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # 连接文本框和滚动条
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)

        # 设置文本框为只读
        self.log_text.config(state=tk.DISABLED)

        # 按钮框架
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        button_frame.grid_columnconfigure(0, weight=1)
        
        # 创建内部框架来居中放置按钮
        inner_button_frame = tk.Frame(button_frame)
        inner_button_frame.grid(row=0, column=0)
        
        tk.Button(inner_button_frame, text="取消", command=self._on_cancel, width=10).pack(side=tk.RIGHT, padx=5)
        tk.Button(inner_button_frame, text="确定", command=self._on_confirm, width=10).pack(side=tk.RIGHT, padx=5)

        # 初始化状态
        update_tag_group_state()
        update_normalize_state()
    
    # 绑定UI，使用set的逻辑函数
    def _on_confirm(self):
        # 验证文件夹路径
        if not self.inputs_dict["folder_path"].get().strip():
            self.show_error("请选择要处理的文件夹")
            return

        if self.on_confirm_callback:
            self.on_confirm_callback()

    def _on_cancel(self):
        if self.on_cancel_callback:
            self.on_cancel_callback()
    # set方法
    def set_on_confirm(self, callback):
        self.on_confirm_callback = callback
        
    def set_on_cancel(self, callback):
        self.on_cancel_callback = callback

    # 传递参数  
    def get_values(self):
        return {k: v.get() for k, v in self.inputs_dict.items()}
        
    def show_error(self, message):
        messagebox.showerror("错误", message)
        
    def run(self):
        self.root.mainloop()
        return self.get_values()
        
    def close(self):
        self.root.destroy()

    def clear_cache(self):
        """清除所有缓存"""
        from src.core.cache_manager import clear_all_cache
        clear_all_cache()
        
    def append_log(self, text):
        """添加日志到文本框"""
        if self.log_text:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, text)
            self.log_text.see(tk.END)  # 自动滚动到底部
            self.root.update()  # 完整更新GUI
            self.log_text.config(state=tk.DISABLED)
            sys.stdout.flush()  # 刷新输出缓冲区

    def clear_log(self):
        """清空日志"""
        if self.log_text:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)

class GuiChannel(InputChannel):
    """图形界面输入通道 - Presenter"""
    
    def __init__(self, loop=None):
        self.view = None
        self.loop = loop or asyncio.get_event_loop()
        self.result = {"confirmed": False, "values": {}}
        self._setup_stdout_redirect()

    def _setup_stdout_redirect(self):
        """设置标准输出重定向"""
        class StdoutRedirector:
            def __init__(self, view_ref):
                self.view_ref = view_ref
                self._original_stdout = sys.stdout

            def write(self, text):
                try:
                    # 确保有原始stdout
                    if self._original_stdout:
                        self._original_stdout.write(text)  # 保持终端输出
                    # 尝试更新GUI
                    if self.view_ref and self.view_ref.view:
                        self.view_ref.view.append_log(text)
                except Exception as primary_error:
                    # 使用更安全的错误处理
                    try:
                        if self._original_stdout:
                            self._original_stdout.write("输出重定向错误: " + str(primary_error) + "\n")
                    except (AttributeError, IOError) as fallback_error:
                        # 如果连错误输出都失败，使用 print 直接输出
                        print("严重错误：输出重定向完全失败:", str(fallback_error))
                        print(text)
            def flush(self):
                self._original_stdout.flush()

        self._original_stdout = sys.stdout  # 保存原始stdout的引用
        self.redirector = StdoutRedirector(self)
        sys.stdout = self.redirector

    def restore_stdout(self):
        """恢复原始的标准输出"""
        if hasattr(self, '_original_stdout'):
            sys.stdout = self._original_stdout
    def collect_inputs(self) -> UserInputs:
        """通过GUI收集用户输入"""
        if not self.view:
            self.view = VndbInputView(loop=self.loop)
            def on_confirm():
                values = self.view.get_values()
                if not values["folder_path"].strip():
                    self.view.show_error("请选择要处理的文件夹")
                    return
                self.view.clear_log()  # 清空之前的日志
                self.result["values"] = values
                self.result["confirmed"] = True
                self.view.root.quit()
                
            def on_cancel():
                self.result["confirmed"] = False
                if self.view:
                    self.view.close()
                    self.view = None
                self.restore_stdout()  # 恢复原始stdout
            
            # 设置回调
            self.view.root.protocol("WM_DELETE_WINDOW", on_cancel)  # 窗口关闭按钮
            self.view.set_on_confirm(on_confirm)
            self.view.set_on_cancel(on_cancel)
        
        # 重置状态并运行
        self.result["confirmed"] = False
        self.view.run()
        
        # 处理结果
        if not self.result["confirmed"] or not self.result["values"].get("folder_path", "").strip():
            # 如果取消了或没有选择文件夹，返回空路径
            if self.view:
                self.view.close()
                self.view = None
            self.restore_stdout()  # 恢复原始stdout
            return UserInputs(folder_path="")
        
        # 返回有效的输入
        return UserInputs(**self.result["values"])