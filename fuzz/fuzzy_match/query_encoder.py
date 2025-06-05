"""
轻量级查询编码器模块

使用ONNX runtime进行推理，将查询文本转换为向量表示
"""
import os
import numpy as np
import onnxruntime as ort
from typing import List
from tokenizers import Tokenizer


class QueryEncoder:
    """轻量级查询编码器"""
    
    def __init__(self, 
                 cache_dir: str,
                 model_name: str = 'paraphrase-multilingual-mpnet-base-v2'):
        """
        初始化编码器
        
        Args:
            cache_dir: 包含encoder.onnx的缓存目录
            model_name: 原始模型名称(用于加载分词器)
        """
        self.model_path = os.path.join(cache_dir, 'encoder.onnx')
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Encoder model not found at {self.model_path}. "
                "Please run build_index.py first."
            )
            
        # 初始化ONNX运行时会话
        self.session = ort.InferenceSession(self.model_path)
        
        # 加载分词器 (使用完整的模型名称)
        tokenizer_path = os.path.join(cache_dir, 'tokenizer')
        self.tokenizer = Tokenizer.from_file(os.path.join(tokenizer_path, "tokenizer.json"))
        
    def encode(self, 
              texts: List[str],
              batch_size: int = 32,
              show_progress_bar: bool = False) -> np.ndarray:
        """
        编码文本列表
        
        Args:
            texts: 待编码的文本列表
            batch_size: 批处理大小
            show_progress_bar: 是否显示进度条(仅占位,实际未实现)
            
        Returns:
            numpy数组,shape为(len(texts), embedding_dim)
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # 对批次进行分词
            # 使用 tokenizers 库的编码方法
            encodings = self.tokenizer.encode_batch(batch_texts)
            
            # 获取最大长度用于填充
            max_len = max(len(enc.ids) for enc in encodings)
            
            # 构建输入张量
            input_ids = []
            attention_mask = []
            
            for enc in encodings:
                # 填充序列到最大长度
                ids = enc.ids + [self.tokenizer.token_to_id("[PAD]")] * (max_len - len(enc.ids))
                mask = [1] * len(enc.ids) + [0] * (max_len - len(enc.ids))
                
                input_ids.append(ids)
                attention_mask.append(mask)
            
            tokens = {
                'input_ids': np.array(input_ids),
                'attention_mask': np.array(attention_mask)
            }
            tokens['input_ids'] = tokens['input_ids'].astype(np.int64)
            tokens['attention_mask'] = tokens['attention_mask'].astype(np.int64)
            
            # 执行ONNX推理
            onnx_inputs = {
                'input_ids': tokens['input_ids'],
                'attention_mask': tokens['attention_mask']
            }
            embeddings = self.session.run(['embedding'], onnx_inputs)[0]
            
            all_embeddings.append(embeddings)
            
        return np.vstack(all_embeddings)
        
    def encode_single(self, text: str) -> np.ndarray:
        """
        编码单个文本
        
        Args:
            text: 待编码的文本
            
        Returns:
            numpy数组,shape为(embedding_dim,)
        """
        return self.encode([text])[0]

if __name__ == '__main__':
    # 使用示例
    cache_dir = os.path.join("fuzz", "cache")
    encoder = QueryEncoder(cache_dir=cache_dir)
    
    # 测试单个查询
    query = "Fate/stay night"
    vector = encoder.encode_single(query)
    print(f"Query shape: {vector.shape}")
    
    # 测试批量查询
    queries = [
        "Fate/stay night",
        "CLANNAD",
        "Steins;Gate"
    ]
    vectors = encoder.encode(queries)
    print(f"Batch shape: {vectors.shape}")