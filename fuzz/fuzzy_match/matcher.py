"""
静态向量索引的标题匹配器模块

使用预构建的FAISS索引和ONNX编码器进行高效的标题匹配
"""
import os
from pathlib import Path
import numpy as np
import faiss
import pickle
from typing import List, Set, Dict, NamedTuple
from .query_encoder import QueryEncoder

class MatchResult(NamedTuple):
    """匹配结果数据类"""
    vn_id: str
    title: str
    score: float
    all_titles: Set[str]

class TitleMatcher:
    """视觉小说标题匹配器"""
    
    def __init__(self,
                 data_path: str,
                 cache_dir: str,
                 threshold: float = 0.75,
                 top_k: int = 5):
        """
        初始化匹配器

        Args:
            data_path: vn_titles数据文件路径(用于兼容性,实际未使用)
            cache_dir: 缓存目录,包含index.faiss和metadata.pkl
            threshold: 匹配分数阈值
            top_k: 返回的最大匹配数量
        """
        self.cache_dir = Path(cache_dir)
        self.threshold = threshold
        self.top_k = top_k
        # 检查缓存文件
        if not self.cache_dir.exists():
            raise FileNotFoundError(
                f"Cache directory not found: {self.cache_dir}"
                "\nPlease run build_index.py first."
            )
            
        # 加载编码器
        self.encoder = QueryEncoder(cache_dir=str(self.cache_dir))
        
        # 加载索引和元数据
        self._load_resources()
        
    def _load_resources(self):
        """加载FAISS索引和元数据"""
        # 加载元数据
        with open(self.cache_dir / "index" / "metadata.pkl", "rb") as f:
            metadata = pickle.load(f)
            
        self.titles = metadata['titles']
        self.title_to_id = metadata['title_to_id']
        self.id_to_titles = metadata['id_to_titles']
        self.dimension = metadata['dimension']
        
        # 加载FAISS索引
        self.index = faiss.read_index(str(self.cache_dir / "index" / "index.faiss"))
    def match(self, query: str) -> List[MatchResult]:
        """
        匹配单个查询标题

        Args:
            query: 查询标题

        Returns:
            匹配结果列表,按相似度降序排序
        """
        # 编码查询文本
        query_vector = self.encoder.encode_single(query).reshape(1, -1)
        
        # 检查向量维度
        if query_vector.shape[1] != self.dimension:
            raise ValueError(f"Query vector dimension {query_vector.shape[1]} does not match index dimension {self.dimension}")
        
        # 搜索最近邻
        distances, indices = self.index.search(query_vector, self.top_k)
        
        # 转换距离为相似度分数
        max_distance = np.max(distances)
        if max_distance == 0:
            scores = np.ones_like(distances)
        else:
            scores = 1 - distances / max_distance
            
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if score >= self.threshold and idx < len(self.titles):
                title = self.titles[idx]
                # 获取该标题对应的所有VN ID
                vn_ids = self.title_to_id[title]
                for vn_id in vn_ids:
                    # 获取该VN的所有标题
                    all_titles = self.id_to_titles[vn_id]
                    results.append(MatchResult(vn_id, title, float(score), all_titles))
                    
        # 按分数降序排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:self.top_k]
    def match_batch(self, queries: List[str]) -> Dict[str, List[MatchResult]]:
        """
        批量匹配多个查询标题

        Args:
            queries: 查询标题列表

        Returns:
            查询到结果的映射字典
        """
        return {query: self.match(query) for query in queries}

if __name__ == '__main__':
    # 使用示例
    matcher = TitleMatcher(
        data_path=os.path.join("fuzz", "data", "vn_titles"),
        cache_dir=os.path.join("fuzz", "cache"),
        threshold=0.75
    )
    
    # 单个查询
    results = matcher.match("Fate/stay night")
    print("Single query results:")
    for r in results:
        print(f"{r.title} (ID: {r.vn_id}, Score: {r.score:.3f})")
        
    # 批量查询
    queries = ["CLANNAD", "Steins;Gate"]
    batch_results = matcher.match_batch(queries)
    print("\nBatch query results:")
    for query, results in batch_results.items():
        print(f"\n{query}:")
        for r in results:
            print(f"{r.title} (ID: {r.vn_id}, Score: {r.score:.3f})")