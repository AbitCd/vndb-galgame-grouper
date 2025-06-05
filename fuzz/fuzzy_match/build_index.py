"""
预构建向量索引和编码器模块

本脚本用于离线构建:
1. FAISS向量索引(.faiss)
2. 标题词表映射(.pkl)  
3. ONNX格式编码器(.onnx)
"""
import os
import torch
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
from typing import List, Set
import onnx
from tqdm import tqdm
import psutil
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError
import hashlib
import json

_FORCE_CPU = None

def _should_use_cpu():
    """检测是否应该使用CPU模式"""
    global _FORCE_CPU
    if _FORCE_CPU is None:
        try:
            import torch
            if not torch.cuda.is_available():
                _FORCE_CPU = True
            else:
                gpu_name = torch.cuda.get_device_name(0).lower()
                _FORCE_CPU = any(x in gpu_name for x in ['uhd', 'graphics', 'integrated'])
        except (ImportError, RuntimeError, AttributeError) as e:
            # ImportError: torch未安装
            # RuntimeError: CUDA运行时错误
            # AttributeError: CUDA相关属性不存在
            print(f"GPU检测失败，使用CPU模式: {e}")
            _FORCE_CPU = True
        if _FORCE_CPU:
            print("Detected low-end GPU, forcing CPU mode for stability")
    return _FORCE_CPU


def load_titles(data_path: str, languages: Set[str] = None) -> List[str]:
    """加载标题数据"""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"数据文件不存在: {data_path}")
    
    languages = languages or {'en', 'ja', 'zh-Hans', 'zh-Hant'}
    titles = []
    title_to_id = {}
    id_to_titles = {}
    
    # 获取总行数用于进度条
    total_lines = sum(1 for _ in open(data_path, 'r', encoding='utf-8'))
    
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in tqdm(f, total=total_lines, desc="加载标题"):
            parts = line.strip().split('\t')
            if len(parts) < 4:
                continue
                
            vn_id, lang, type_, title = parts[:4]
            if lang not in languages:
                continue
                
            titles.append(title)
            
            if title not in title_to_id:
                title_to_id[title] = set()
            title_to_id[title].add(vn_id)
            
            if vn_id not in id_to_titles:
                id_to_titles[vn_id] = set()
            id_to_titles[vn_id].add(title)
    
    return titles, title_to_id, id_to_titles

def save_with_progress(data, file_path: str, desc: str):
    """使用进度条保存大文件"""
    total_size = len(pickle.dumps(data))  # 估算大小
    with tqdm(total=total_size, desc=desc, unit='B', unit_scale=True) as pbar:
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
            pbar.update(total_size)
def compute_title_hash(title):
    """计算标题的哈希值"""
    return hashlib.md5(title.encode('utf-8')).hexdigest()

def load_cache(cache_dir):
    """加载缓存数据"""
    cache_file = os.path.join(cache_dir, "cache_info.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载缓存文件失败: {e}")
            return {'version': '1.0', 'title_hashes': {}, 'last_update': None}
    return {'version': '1.0', 'title_hashes': {}, 'last_update': None}

def save_cache(cache_dir, cache_data):
    """保存缓存数据"""
    cache_file = os.path.join(cache_dir, "cache_info.json")
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)

class TextEncoder:
    def __init__(self, model_name: str):
        self.model_name = model_name  # 保存模型名称
        self.model = SentenceTransformer(model_name, local_files_only=True)
        
    def _encode_batch(self, titles_batch):
        try:
            # 在进程内部初始化model
            local_model = SentenceTransformer(self.model_name, local_files_only=True)
            
            if _should_use_cpu():
                device = torch.device("cpu")
            else:
                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            local_model.to(device)

            # 将大批次分成更小的子批次处理
            sub_batch_size = 8  # 更小的批处理大小
            all_embeddings = []

            for i in range(0, len(titles_batch), sub_batch_size):
                sub_batch = titles_batch[i:i + sub_batch_size]
                with torch.no_grad():
                    emb = local_model.encode(
                        sub_batch,
                        batch_size=sub_batch_size,
                        show_progress_bar=False,
                        convert_to_tensor=True
                    ).cpu().numpy().astype(np.float32)
                    all_embeddings.append(emb)

                # 主动进行内存清理
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

            # 清理资源
            del local_model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            return np.concatenate(all_embeddings, axis=0)

        except Exception as e:
            print(f"Batch encoding failed: {e}")
            return None

    def encode_parallel(self, titles, n_workers=4):
        print(f"Starting parallel encoding with {n_workers} workers")
        batch_size = 1000
        batches = [titles[i:i + batch_size] for i in range(0, len(titles), batch_size)]
        print(f"Split into {len(batches)} batches")
        
        embeddings_list = []
        with ProcessPoolExecutor(max_workers=2) as executor:
            futures = []
            for batch in batches:
                future = executor.submit(self._encode_batch, batch)
                futures.append(future)
            
            for i, future in enumerate(tqdm(as_completed(futures), total=len(futures), desc="Processing batches")):
                try:
                    result = future.result(timeout=300)  # 5分钟超时
                    if result is not None:
                        embeddings_list.append(result)
                    else:
                        print(f"Batch {i} failed, skipping...")
                except TimeoutError:
                    print(f"Batch {i} timed out, skipping...")
                    continue
                except Exception as e:
                    print(f"Error processing batch {i}: {e}")
                    continue
                
                # 定期显示内存使用情况
                if i % 10 == 0:
                    process = psutil.Process()
                    print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
        
        if not embeddings_list:
            raise RuntimeError("All batches failed to process")
        
        return np.concatenate(embeddings_list, axis=0)
            
    def encode(self, titles):
        return self.model.encode(titles, show_progress_bar=True, batch_size=32, convert_to_numpy=True)

def export_encoder(model_name: str, output_dir: str):
    """导出编码器为ONNX格式"""
    import torch.nn as nn
    
    class EncoderModule(nn.Module):
        def __init__(self, model):
            super().__init__()
            self.transformer = model._first_module().auto_model
            self.pooling = model._modules['1']
        
        def forward(self, input_ids, attention_mask):
            # 获取transformer输出
            outputs = self.transformer(input_ids=input_ids, attention_mask=attention_mask)
            # 进行pooling
            pooled = self.pooling({
                'token_embeddings': outputs.last_hidden_state,
                'attention_mask': attention_mask
            })
            # 返回句子embedding
            return pooled['sentence_embedding']

    # 加载模型
    model = SentenceTransformer(model_name, local_files_only=True)
    
    # 创建完整的编码器模块
    encoder = EncoderModule(model)
    encoder.eval()
    
    # 准备示例输入
    tokens = model.tokenizer(["example"],
                         padding=True,
                         truncation=True,
                         return_tensors="pt")

    # 导出ONNX模型
    output_path = os.path.join(output_dir, "encoder.onnx")
    torch.onnx.export(encoder,
                     args=(tokens['input_ids'], tokens['attention_mask']),
                     f=output_path,
                     input_names=['input_ids', 'attention_mask'],
                     output_names=['embedding'],
                     dynamic_axes={'input_ids': {0: 'batch', 1: 'sequence'},
                                 'attention_mask': {0: 'batch', 1: 'sequence'},
                                 'embedding': {0: 'batch'}},
                    opset_version=14)
    
    # 验证导出的模型
    onnx_model = onnx.load(output_path)
    onnx.checker.check_model(onnx_model)

def build_faiss_index(vectors: np.ndarray, dimension: int) -> faiss.Index:
    """构建FAISS索引"""
    nlist = min(4096, max(100, int(len(vectors) / 40)))  # 动态设置聚类中心数
    quantizer = faiss.IndexFlatL2(dimension)
    index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_L2)
    
    print("训练索引...", flush=True)
    index.train(vectors)
    
    print("添加向量到索引...", flush=True)
    batch_size = 10000
    for i in tqdm(range(0, len(vectors), batch_size), desc="构建索引"):
        batch = vectors[i:i + batch_size]
        index.add(batch)
    
    # 设置搜索参数
    index.nprobe = min(64, max(10, nlist // 8))
    
    return index

def main():
    try:
        # 配置
        model_name = 'paraphrase-multilingual-mpnet-base-v2'
        data_path = os.path.join("fuzz", "data", "vn_tl00")
        output_dir = os.path.join("fuzz", "cache")
        os.makedirs(output_dir, exist_ok=True)

        print("开始加载标题...", flush=True)
        titles, title_to_id, id_to_titles = load_titles(data_path)
        print(f"成功加载 {len(titles)} 个标题", flush=True)

        # 加载缓存
        cache_data = load_cache(output_dir)
        
        # 检查需要更新的标题
        new_title_hashes = {title: compute_title_hash(title) for title in titles}
        titles_to_update = []
        cached_vectors = []
        
        encoder_dir = os.path.join(output_dir, "encoder")
        embeddings_path = os.path.join(encoder_dir, "embeddings.pkl")
        
        # 如果存在之前的向量数据，加载它
        existing_vectors = None
        if os.path.exists(embeddings_path):
            try:
                with open(embeddings_path, 'rb') as f:
                    existing_vectors = pickle.load(f)
            except (pickle.UnpicklingError, IOError) as e:
                print(f"无法加载现有向量数据，将重新生成所有向量: {e}")
                existing_vectors = None
        
        # 确定需要更新的标题
        for i, title in enumerate(titles):
            title_hash = new_title_hashes[title]
            if title not in cache_data['title_hashes'] or cache_data['title_hashes'][title] != title_hash:
                titles_to_update.append(title)
            elif existing_vectors is not None:
                cached_vectors.append(existing_vectors[i])
        
        if titles_to_update:
            print(f"需要更新 {len(titles_to_update)} 个标题的向量", flush=True)
            print("开始编码新文本...", flush=True)
            encoder = TextEncoder(model_name)
            try:
                new_vectors = encoder.encode_parallel(titles_to_update)
            except Exception as e:
                print(f"Parallel encoding failed, falling back to sequential processing: {e}")
                new_vectors = encoder.encode(titles_to_update)
                
            # 更新缓存
            for title, title_hash in new_title_hashes.items():
                cache_data['title_hashes'][title] = title_hash
            
            # 合并向量
            if cached_vectors:
                vectors = np.concatenate([cached_vectors, new_vectors], axis=0)
            else:
                vectors = new_vectors
        else:
            print("所有标题都是最新的，使用缓存的向量数据", flush=True)
            vectors = existing_vectors
            
        # 询问是否导出编码器
        print("开始导出编码器...", flush=True)
        user_input = input("是否要导出编码器? (y/n): ").strip().lower()
        if user_input == 'y':
            export_encoder(model_name, output_dir)
            print("编码器导出完成", flush=True)
        else:
            print("跳过导出编码器")
            
        if vectors is None:
            raise ValueError("无法获取向量数据")

        print(f"文本编码完成，维度: {vectors.shape}", flush=True)

        print("构建索引...", flush=True)
        index = build_faiss_index(vectors, dimension=vectors.shape[1])
        print("索引构建完成", flush=True)

        print("保存数据...", flush=True)
        try:
            # 保存向量
            os.makedirs(encoder_dir, exist_ok=True)
            save_with_progress(vectors, embeddings_path, "保存向量数据")
            print("向量数据已保存", flush=True)

            # 保存索引
            index_dir = os.path.join(output_dir, "index")
            os.makedirs(index_dir, exist_ok=True)
            index_path = os.path.join(index_dir, "index.faiss")
            print("正在保存索引...", flush=True)
            with tqdm(total=1, desc="保存索引") as pbar:
                faiss.write_index(index, index_path)
                pbar.update(1)
            print("索引已保存", flush=True)

            # 保存元数据
            metadata_path = os.path.join(index_dir, "metadata.pkl")
            metadata = {
                'title_to_id': title_to_id,
                'id_to_titles': id_to_titles,
                'dimension': vectors.shape[1],
                'titles': titles
            }
            save_with_progress(metadata, metadata_path, "保存元数据")
            print("元数据已保存", flush=True)
            
            # 保存缓存信息
            save_cache(output_dir, cache_data)
            print("缓存信息已更新", flush=True)

            print("所有处理已完成", flush=True)
            print(f"文件保存位置: {output_dir}")
            print(f" - 编码器: {os.path.join('encoder', 'encoder.onnx')}")
            print(f" - 向量: {os.path.join('encoder', 'embeddings.pkl')}")
            print(f" - 索引: {os.path.join('index', 'index.faiss')}")
            print(f" - 元数据: {os.path.join('index', 'metadata.pkl')}")

        except (IOError, OSError) as e:
            print(f"保存数据时出错: {str(e)}", flush=True)
            return

    except FileNotFoundError as e:
        print(f"错误: {str(e)}", flush=True)
        return
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}", flush=True)
        return

if __name__ == '__main__':
    main()