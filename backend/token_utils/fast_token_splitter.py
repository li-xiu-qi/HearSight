"""
高性能Token分块器
优化了token计算和字符串操作的性能
"""
import re
from typing import List, Optional, Tuple
from .calculate_tokens import TokenCalculator, OpenAITokenCalculator


class FastTokenSplitter:
    """
    高性能的Token分块器，优化了以下方面：
    1. 减少token计算次数
    2. 优化字符串操作
    3. 使用二分查找确定分块边界
    4. 缓存token计算结果
    """
    
    def __init__(
        self,
        token_calculator: TokenCalculator,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        self.token_calculator = token_calculator
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 优化的分隔符列表，按优先级排序
        self.separators = separators or [
            "\n\n",  # 段落分隔
            "。", "！", "？", "；",  # 中文句子结束
            ". ", "! ", "? ", "; ",  # 英文句子结束
            "\n",  # 行分隔
            "，", "、", ", ",  # 短语分隔
            " ",  # 词分隔
        ]
        
        # Token计算缓存
        self._token_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
    
    def _get_token_count_cached(self, text: str) -> int:
        """带缓存的token计算"""
        if text in self._token_cache:
            self._cache_hits += 1
            return self._token_cache[text]
        
        self._cache_misses += 1
        count = self.token_calculator.count_tokens(text)
        
        # 限制缓存大小，避免内存泄漏
        if len(self._token_cache) > 10000:
            # 清理一半的缓存
            keys_to_remove = list(self._token_cache.keys())[:5000]
            for key in keys_to_remove:
                del self._token_cache[key]
        
        self._token_cache[text] = count
        return count
    
    def _find_best_split_point(self, text: str, max_chars: int) -> int:
        """
        使用二分查找找到最佳分割点
        返回不超过token限制的最大字符位置
        """
        if len(text) <= max_chars:
            if self._get_token_count_cached(text) <= self.chunk_size:
                return len(text)
        
        # 二分查找最佳分割点
        left, right = 0, min(len(text), max_chars)
        best_pos = 0
        
        while left <= right:
            mid = (left + right) // 2
            chunk = text[:mid]
            
            if self._get_token_count_cached(chunk) <= self.chunk_size:
                best_pos = mid
                left = mid + 1
            else:
                right = mid - 1
        
        return best_pos
    
    def _find_separator_near_position(self, text: str, target_pos: int, search_range: int = 200) -> int:
        """
        在目标位置附近寻找最佳的分隔符位置
        """
        # 搜索范围：target_pos前后search_range个字符
        start_search = max(0, target_pos - search_range)
        end_search = min(len(text), target_pos + search_range)
        search_text = text[start_search:end_search]
        
        best_pos = target_pos
        best_priority = len(self.separators)  # 最低优先级
        
        for priority, separator in enumerate(self.separators):
            # 从目标位置向前搜索分隔符
            for match in re.finditer(re.escape(separator), search_text):
                abs_pos = start_search + match.end()  # 分隔符后的位置
                
                # 优先选择更接近目标位置且优先级更高的分隔符
                if priority < best_priority or (priority == best_priority and abs(abs_pos - target_pos) < abs(best_pos - target_pos)):
                    # 确保分割后的chunk不超过token限制
                    if self._get_token_count_cached(text[:abs_pos]) <= self.chunk_size:
                        best_pos = abs_pos
                        best_priority = priority
        
        return best_pos
    
    def split_text(self, text: str) -> List[str]:
        """
        高性能文本分割
        """
        if not text:
            return []
        
        # 如果整个文本都在限制内，直接返回
        if self._get_token_count_cached(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        current_pos = 0
        text_len = len(text)
        
        # 估算每个token的平均字符数（用于初始估算）
        sample_text = text[:min(1000, len(text))]
        sample_tokens = self._get_token_count_cached(sample_text)
        avg_chars_per_token = len(sample_text) / max(sample_tokens, 1)
        estimated_chars_per_chunk = int(self.chunk_size * avg_chars_per_token * 1.2)  # 留一些余量
        
        while current_pos < text_len:
            # 估算这个chunk的结束位置
            estimated_end = min(current_pos + estimated_chars_per_chunk, text_len)
            
            # 使用二分查找找到精确的分割点
            relative_end = self._find_best_split_point(
                text[current_pos:], 
                estimated_end - current_pos
            )
            absolute_end = current_pos + relative_end
            
            # 如果不是最后一个chunk，尝试在分隔符处分割
            if absolute_end < text_len:
                better_end = self._find_separator_near_position(
                    text, absolute_end, search_range=min(200, estimated_chars_per_chunk // 4)
                )
                if better_end > current_pos:  # 确保有进展
                    absolute_end = better_end
            
            # 提取chunk
            chunk = text[current_pos:absolute_end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 移动到下一个位置
            if absolute_end == current_pos:  # 避免死循环
                current_pos += 1
            else:
                current_pos = absolute_end
        
        # 添加重叠（如果需要）
        if self.chunk_overlap > 0 and len(chunks) > 1:
            chunks = self._add_overlap_optimized(chunks)
        
        return chunks
    
    def _add_overlap_optimized(self, chunks: List[str]) -> List[str]:
        """
        优化的重叠添加，减少字符串操作
        """
        if not chunks or len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            current_chunk = chunks[i]
            
            # 计算重叠部分
            if len(prev_chunk) > self.chunk_overlap:
                overlap = prev_chunk[-self.chunk_overlap:]
            else:
                overlap = prev_chunk
            
            # 组合chunk
            combined = overlap + current_chunk
            
            # 如果组合后超过token限制，减少重叠
            if self._get_token_count_cached(combined) > self.chunk_size:
                # 二分查找合适的重叠长度
                left, right = 0, len(overlap)
                best_overlap_len = 0
                
                while left <= right:
                    mid = (left + right) // 2
                    test_overlap = overlap[-mid:] if mid > 0 else ""
                    test_combined = test_overlap + current_chunk
                    
                    if self._get_token_count_cached(test_combined) <= self.chunk_size:
                        best_overlap_len = mid
                        left = mid + 1
                    else:
                        right = mid - 1
                
                if best_overlap_len > 0:
                    final_overlap = overlap[-best_overlap_len:]
                    overlapped_chunks.append(final_overlap + current_chunk)
                else:
                    overlapped_chunks.append(current_chunk)
            else:
                overlapped_chunks.append(combined)
        
        return overlapped_chunks
    
    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": f"{hit_rate:.2%}",
            "cache_size": len(self._token_cache)
        }
    
    def clear_cache(self):
        """清空缓存"""
        self._token_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0


# 便捷函数
def fast_split_text(
    text: str,
    token_calculator: TokenCalculator,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[str]:
    """
    便捷的文本分割函数
    """
    splitter = FastTokenSplitter(
        token_calculator=token_calculator,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_text(text)


# 性能测试函数
def benchmark_splitters(text: str, token_calculator: TokenCalculator, chunk_size: int = 500):
    """
    对比新旧分割器的性能
    """
    import time
    
    print("🔬 性能测试开始...")
    print(f"📄 文本长度: {len(text)} 字符")
    print(f"🎯 目标chunk大小: {chunk_size} tokens")
    
    # 测试新的快速分割器
    print("\n🚀 测试 FastTokenSplitter...")
    fast_splitter = FastTokenSplitter(token_calculator, chunk_size=chunk_size)
    
    start_time = time.time()
    fast_chunks = fast_splitter.split_text(text)
    fast_time = time.time() - start_time
    
    fast_stats = fast_splitter.get_cache_stats()
    
    print(f"   ⏱️  耗时: {fast_time:.3f}秒")
    print(f"   📊 生成chunks: {len(fast_chunks)}")
    print(f"   🎯 缓存命中率: {fast_stats['hit_rate']}")
    print(f"   💾 缓存大小: {fast_stats['cache_size']}")
    
    # 测试原始的递归分割器
    print("\n🐌 测试 RecursiveTokenTextSplitter...")
    from .recursive_token_splitter import RecursiveTokenTextSplitter
    recursive_splitter = RecursiveTokenTextSplitter(token_calculator, chunk_size=chunk_size)
    
    start_time = time.time()
    recursive_chunks = recursive_splitter.split_text(text)
    recursive_time = time.time() - start_time
    
    print(f"   ⏱️  耗时: {recursive_time:.3f}秒")
    print(f"   📊 生成chunks: {len(recursive_chunks)}")
    
    # 性能对比
    speedup = recursive_time / fast_time if fast_time > 0 else float('inf')
    print(f"\n📈 性能提升: {speedup:.1f}x 倍")
    
    return {
        "fast_time": fast_time,
        "recursive_time": recursive_time,
        "speedup": speedup,
        "fast_chunks": len(fast_chunks),
        "recursive_chunks": len(recursive_chunks)
    }


if __name__ == "__main__":
    # 简单测试
    from .calculate_tokens import OpenAITokenCalculator
    
    calculator = OpenAITokenCalculator()
    test_text = "这是一个测试文本。" * 1000  # 创建一个较长的测试文本
    
    # 运行性能测试
    benchmark_splitters(test_text, calculator, chunk_size=200)