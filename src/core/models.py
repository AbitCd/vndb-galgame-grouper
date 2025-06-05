"""
使用Pydantic定义的数据模型
"""
import os
from typing import Dict, Any
from pydantic import BaseModel, Field, validator

class UserInputs(BaseModel):
    """用户输入参数模型"""
    # 基础配置
    debug_mode: bool = Field(default=False, description="是否开启调试模式")
    regex_filter: str = Field(default="", description="用于过滤目录名的正则表达式")
    enable_fuzzy_match: bool = Field(default=True, description="是否启用模糊匹配")
    fuzzy_match_threshold: float = Field(default=0.4, description="模糊匹配阈值")
    
    @validator("fuzzy_match_threshold")
    def validate_fuzzy_match_threshold(cls, v: float, values: Dict[str, Any]) -> float:
        """验证模糊匹配阈值的合法性"""
        if values.get("enable_fuzzy_match"):
            try:
                v = float(v)
                if not 0 <= v <= 1:
                    raise ValueError("模糊匹配阈值必须在0到1之间")
            except ValueError as e:
                raise ValueError("模糊匹配阈值必须是0到1之间的有效浮点数") from e
        return v
    
    # 缓存操作
    clear_cache: bool = Field(default=False, description="是否清除所有缓存")
    # 缓存设置
    api_cache: bool = Field(default=True, description="是否启用API查询缓存")
    group_cache: bool = Field(default=True, description="是否启用分组结果缓存")
    
    # 文件夹路径
    folder_path: str = Field(default="", description="待处理的文件夹路径")
    
    # 分组设置
    do_vn_group: bool = Field(default=True, description="是否将文件夹分为VisualNovel/NotMatched两组")
    do_tag_grouping: bool = Field(default=False, description="是否进行标签分组")
    tag_group_field: str = Field(default="", description="要分组的标签字段")
    rename_to_original: bool = Field(default=False, description="是否将分组文件夹名替换为原名")
    
    # 命名规范
    normalize_name: bool = Field(default=False, description="是否将文件夹名称规范化为通用名称")
    normalize_strict: bool = Field(default=False, description="是否严格规范化（仅保留通用名）")
    
    # 自定义参数
    custom_params: Dict[str, Any] = Field(default_factory=dict, description="自定义扩展参数")
    
    # 验证器保持不变
    @validator('tag_group_field')
    def validate_tag_group_field(cls, v, values):
        if v and not values.get('do_tag_grouping', False):
            raise ValueError("必须启用标签分组（输入7）后才能指定分组标签（输入8）")
        return v
    
    @validator('rename_to_original')
    def validate_rename_to_original(cls, v, values):
        if v and not values.get('tag_group_field'):
            raise ValueError("必须填写分组标签（输入8）后才能替换为原名（输入9）")
        return v
    
    @validator('normalize_strict')
    def validate_normalize_strict(cls, v, values):
        if v and not values.get('normalize_name', False):
            raise ValueError("必须启用规范化（输入10）后才能启用严格规范（输入11）")
        return v
    
    @validator('folder_path')
    def validate_folder_path(cls, v):
        if not v:
            return ""
        if not os.path.isdir(v):
            raise ValueError(f"文件夹路径无效或不存在：{v}。请提供一个有效的目录路径。")
        return v

    @validator('regex_filter')
    def validate_regex_filter(cls, v):
        import re
        if not v:
            return ""
        try:
            re.compile(v)
        except re.error:
            raise ValueError(f"无效的正则表达式：{v}")
        return v

    @validator('*')
    def validate_boolean_fields(cls, v, field):
        if field.type_ is bool and v is None:
            return False
        return v

    @validator('*')
    def validate_dependencies(cls, v, values, field):
        if field.name == 'tag_group_field' and v and not values.get('do_tag_grouping'):
            raise ValueError("必须先启用标签分组才能指定分组标签")
        if field.name == 'rename_to_original' and v and not values.get('tag_group_field'):
            raise ValueError("必须先指定分组标签才能启用原名替换")
        return v

    def get_requirement_types(self) -> list:
        """
        根据用户设置确定所需的API请求类型组合

        Returns:
            list: 请求类型列表，可能包含：
                1: 标题信息 (用于名称规范化/严格规范化/基础文件夹分组)
                2: 开发者和工作人员信息 (用于标签分组)
                3: 详细信息 (用于替换为原名)
        """
        types = set()
        
        # 基础分组和规范化需要type 1
        if self.normalize_name or self.normalize_strict or self.do_vn_group:
            types.add(1)
            
        # 标签分组需要type 2
        if self.do_tag_grouping:
            types.add(2)
            
        # 替换为原名需要type 3
        if self.rename_to_original:
            types.add(3)
            
        # 如果没有任何功能启用，默认使用type 1
        if not types:
            types.add(1)
            
        return sorted(list(types))

    def pre_execution_validation(self) -> None:
        """执行操作前的完整验证
        
        验证所有必要的参数是否有效，包括：
        - 文件夹路径是否存在且可访问
        - 标签字段是否有效
        - 其他参数的合法性
        
        Raises:
            ValueError: 当验证失败时抛出，包含具体的错误信息
        """
        # 验证文件夹路径
        if not self.folder_path:
            raise ValueError("必须提供文件夹路径")
        if not os.path.exists(self.folder_path):
            raise ValueError(f"文件夹路径不存在: {self.folder_path}")
        if not os.path.isdir(self.folder_path):
            raise ValueError(f"指定路径不是一个文件夹: {self.folder_path}")
        if not os.access(self.folder_path, os.R_OK):
            raise ValueError(f"无法访问文件夹，请检查权限: {self.folder_path}")

        # 验证标签相关参数
        if not self.do_tag_grouping and self.tag_group_field:
            raise ValueError("启用标签分组后才能指定标签字段")
        if self.rename_to_original and not self.tag_group_field:
            raise ValueError("使用原名重命名必须指定标签字段")

        # 验证规范化参数
        if self.normalize_strict and not self.normalize_name:
            raise ValueError("使用严格规范化必须同时启用名称规范化")

    class Config:
        """Pydantic配置"""
        title = "VNDB处理工具用户输入"
        json_schema_extra = {
            "example": {
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
                "enable_fuzzy_match": True,
                "fuzzy_match_threshold": 0.4
            }
        }