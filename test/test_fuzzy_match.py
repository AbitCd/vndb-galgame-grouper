"""
测试fuzzy_match模块的标题匹配功能

这个测试脚本演示了如何使用TitleMatcher进行单个和批量的标题匹配。

使用方法:
    在项目根目录直接运行此脚本：python -m test.test_fuzzy_match
"""

import sys
from pathlib import Path


def init_path():
    project_root = Path(__file__).parent.parent
    sys.path.append(str(project_root))
    return project_root

def main():
    from fuzz.fuzzy_match import TitleMatcher
    

    # 初始化匹配器
    matcher = TitleMatcher(
        data_path="fuzz/data/vn_titles",
        cache_dir="fuzz/cache",
        threshold=0.4
    )

    # 单个标题匹配
    results = matcher.match("Fate/stay night")
    print("\n单个标题匹配结果:")
    print(results)

    # 批量标题匹配
    queries = ["CLANNAD", "Steins;Gate"]
    results = matcher.match_batch(queries)
    print("\n批量标题匹配结果:") 
    print(results)


if __name__ == "__main__":
    init_path()
    main()