# VNDB处理工具使用说明

## 简介

本工具用于处理VNDB相关文件夹，支持多种输入方式（GUI、命令行、配置文件、API）。

## 使用方式

### 1. 图形界面（默认）

直接运行程序：

```bash
python main.py
```

### 2. 命令行交互

运行以下命令：

```bash
python main.py --cli
```

### 3. 配置文件

首先生成配置文件示例：

```bash
python tools/generate_config.py config --type json --output myconfig
```

这将生成一个包含所有可用选项的配置文件，包括：
- 基本配置（debug_mode、folder_path等）
- 模糊匹配配置（enable_fuzzy_match、fuzzy_match_threshold）
- 分组配置（do_vn_group、do_tag_grouping等）
- 命名配置（normalize_name、normalize_strict）
- 缓存配置（api_cache、group_cache、clear_cache）

编辑生成的配置文件，然后使用：

```bash
python main.py --config myconfig.json
```

### 4. 命令行参数

运行以下命令：

```bash
python main.py --folder /path/to/folder --debug --normalize --rename-original --tag-field staff.art --enable-fuzzy-match --fuzzy-threshold 0.4
```

常用命令行参数组合示例：

基础使用：
```bash
python main.py --folder /path/to/folder
```

启用模糊匹配：
```bash
python main.py --folder /path/to/folder --enable-fuzzy-match --fuzzy-threshold 0.5
```

完整分组和命名：
```bash
python main.py --folder /path/to/folder --do-vn-group --tag-field developers --normalize
```

### 5. API服务（未实现）

启动API服务器：

```bash
python tools/generate_config.py server
```

然后可以通过HTTP请求调用：

```bash
curl -X POST http://localhost:8080/api/process -H "Content-Type: application/json" -d '{"folder_path":"/path/to/folder","debug_mode":true}'
```

## 参数说明

以下是主要参数的说明：

- debug_mode: 是否开启调试模式
- regex_filter: 用于过滤目录名的正则表达式
- api_cache: 是否启用API查询缓存
- group_cache: 是否启用分组结果缓存
- clear_cache: 是否在处理前清除缓存
- folder_path: 待处理的文件夹路径
- do_vn_group: 是否将文件夹分为VisualNovel/NotMatched两组
- do_tag_grouping: 是否进行标签分组
- tag_group_field: 要分组的标签字段（如developers或staff.art）
- rename_to_original: 是否将分组文件夹名替换为原名
- normalize_name: 是否将文件夹名称规范化为通用名称
- normalize_strict: 是否严格规范化（仅保留通用名）
- enable_fuzzy_match: 是否启用模糊匹配
- fuzzy_match_threshold: 模糊匹配阈值（0~1之间）
## 模糊匹配说明

模糊匹配功能可以帮助更准确地识别游戏文件夹名称：

- 当enable_fuzzy_match=True时，程序会尝试将文件夹名与VNDB数据库中的游戏名进行模糊匹配
- 使用的数据库截至2025年5月，包含了约6.5万条游戏记录
- 匹配一项的平均时间是4s左右（本地测试的结果）
- fuzzy_match_threshold控制匹配精度，取值范围0~1：
  - 值越大要求匹配越精确
  - 推荐值为0.4，可根据实际情况调整
  - 低于0.3可能导致错误匹配
  - 高于0.7可能导致大部分正确项无法匹配

开启调试模式（debug_mode=True）时，会显示更多匹配相关信息，包括：
- 每个文件夹的匹配结果
- 匹配的相似度分数
- 其他可能的匹配选项

注意：如果模糊匹配无法找到合适的结果，将保留原始文件夹名称。

## 参数依赖关系

- 输入8(tag_group_field)需要输入7(do_tag_grouping)为True
- 输入9(rename_to_original)需要输入8(tag_group_field)非空
- 输入11(normalize_strict)需要输入10(normalize_name)为True
- fuzzy_match_threshold仅在enable_fuzzy_match为True时生效
- 模糊匹配的调试信息仅在debug_mode为True时显示

建议使用顺序：
1. 首先配置基础选项（debug_mode、folder_path）
2. 根据需要开启模糊匹配（enable_fuzzy_match和fuzzy_match_threshold）
3. 配置分组选项（do_vn_group和do_tag_grouping）
4. 最后配置命名选项（normalize_name和normalize_strict）

## 注意事项

1. 基础要求
- 请确保在使用本工具之前，已经正确安装了所有依赖项
- 确保文件夹路径正确无误且具有读写权限
- 建议在处理大量文件前先在小规模测试

2. 模糊匹配相关
- 首次使用模糊匹配时会加载模型，可能需要一些时间
- 建议从默认阈值0.4开始尝试，根据实际效果调整
- 如果发现匹配结果不理想，可以：
  - 调整fuzzy_match_threshold值
  - 开启debug_mode查看详细匹配信息
  - 使用regex_filter预处理文件夹名称

3. 性能优化
- 启用缓存（api_cache和group_cache）可以提升重复分组处理速度
- 如果缓存导致问题，可以使用clear_cache参数清除

1. 分组和命名
- 建议先使用do_vn_group进行基础分组
- tag_group_field支持多级字段（如staff.art）
- normalize_strict模式会显著改变文件夹名称，请谨慎使用



## 联系方式

如果遇到任何问题或需要帮助，欢迎通过以下方式联系：
- 项目Issue页面


感谢您的使用！