# VNDB Galgame Grouper

[![License](https://img.shields.io/github/license/AbitCd/vndb-galgame-grouper)](LICENSE.txt)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Code Style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black)
[![Downloads](https://img.shields.io/github/downloads/AbitCd/vndb-galgame-grouper/total)](https://github.com/AbitCd/vndb-galgame-grouper/releases)

一个视觉小说(galgame)文件夹管理工具，支持批量筛选数据库内的视觉小说文件夹，按导演、声优等标签分组，文件夹自动重命名为视觉小说的主要名称。基于VNDB API开发，提供多种使用方式和灵活的配置选项。

[English](README_en.md) | 简体中文 | [日本語](README_ja.md)

---

## ✨ 功能

- 🎮 自动识别在VNDB数据库内的galgame文件夹
  - 支持模糊匹配，模糊匹配容错率较低，平均3s一项
  - 输入正则表达式~~自己动~~自动识别多种命名格式
  - 可配置的匹配精度

- 📂 分组功能
  - 自动区分VN(Visual Novel)和非VN内容
  - 支持按开发商、制作人员等分组

- 🔄 文件重夹命名
  - 支持规范化命名
  - 可选择使用原名或通用名
  - 保留重要标识信息

- 💡 多种使用方式
  - 直观的图形界面
  - 命令行工具
  - 配置文件支持



### 使用示例

```python
# 基础分组示例
python main.py --folder ./games --do-vn-group

# 开发商分组示例
python main.py --folder ./games --tag-field developers

# 完整功能示例
python main.py --folder ./games \
    --enable-fuzzy-match \
    --fuzzy-threshold 0.4 \
    --do-vn-group \
    --tag-field developers \
    --normalize \
    --api-cache
```

这些图片和示例展示了工具的主要功能和使用方式。每个功能都可以根据需求自定义配置，详细设置请参考 [usage.md](usage.md)。

## 💻 系统要求

- Python 3.8 或更高版本
- 支持的操作系统：
  - Windows 10/11
  - Linux (Ubuntu 18.04+, CentOS 7+)
  - macOS 10.15+
- 内存：至少2GB RAM（推荐4GB+）
- 磁盘空间：至少1GB可用空间（用于缓存和索引）

## ⚡ 性能优化

- 采用离线构建的静态资源加载模糊匹配，无需在线加载
- 建议启用缓存以提升重复分组时处理速度：
  ```bash
  python main.py --folder /path/to/games --api-cache --group-cache
  ```
- 处理大量文件时的建议：
  - 适当调整模糊匹配阈值

## 🚀 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 运行工具
```bash
# 图形界面模式
python main.py

# 命令行模式
python main.py --cli
```

3. 基础使用示例
```bash
# 处理指定文件夹
python main.py --folder /path/to/games

# 启用模糊匹配
python main.py --folder /path/to/games --enable-fuzzy-match

# 完整功能示例
python main.py --folder /path/to/games --do-vn-group --tag-field developers --normalize
```

## 📊 项目结构

```
├── src/                # 核心源代码
│   ├── api/           # API服务(未实现)
│   ├── cli/           # 命令行接口(未实现)
│   ├── core/          # 核心功能模块
│   ├── gui/           # 图形界面实现
│   └── templates/     # 配置模板
├── fuzz/              # 模糊匹配模块
│   └── fuzzy_match/   # 匹配算法实现
├── tools/             # 辅助工具
└── scripts/           # 构建脚本
```

## 📖 详细文档

详细使用说明请参考 [usage.md](usage.md)

## 🛠 开发

### 环境准备

推荐使用Python 3.8+，并安装必要的开发依赖：

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
python -m pytest
```

## 🤝 贡献

欢迎任何形式的贡献：

1. Fork 本项目
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 发起 Pull Request

## 📝 许可证

本项目基于 GPLv3 许可证，详情请见 [LICENSE](LICENSE.txt) 文件。

## ⭐ Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=AbitCd/vndb-galgame-grouper&type=Date)](https://star-history.com/#AbitCd/vndb-galgame-grouper&Date)

## 📧 联系方式

如有任何问题或建议，欢迎通过以下方式联系：

- 在 GitHub 上提出 Issue


## ❓ 常见问题

1. **模糊匹配准确率不够理想？**
   - 尝试调整 fuzzy_match_threshold 参数（默认0.4）
   - 使用 regex_filter 预处理文件夹名称
   - 开启 debug_mode 查看详细匹配信息

2. **处理速度较慢？**
   - 检查网络连接状况
   - 模糊匹配本来就慢一点

3. **如何处理特殊字符？**
   - 默认支持日文和中文字符
   - 已经使用 normalize_name 规范化处理了
   - 必要时可以自定义正则过滤

4. **文件夹权限问题？**
   - 确保有读写权限
   - 使用管理员权限运行
   - 检查文件系统权限设置

更多问题请提交 Issue。
## ⭐ 备注
偷懒用AI写的，真会有人看英语版和日语版说明吗？