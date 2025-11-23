from abc import ABC, abstractmethod
from typing import List, Dict
from typing import Dict, List


class TokenCalculator(ABC):
    """
    抽象基类，用于计算文本的token数量
    """
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        计算并返回给定文本的token数量
        """
        pass
    
    def calculate_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        计算一系列消息的token总数
        """
        return sum(self.count_tokens(msg.get('content', '')) for msg in messages)


_global_tokenizers = {}

class TransformerTokenCalculator(TokenCalculator):
    """
    基于Transformer模型的token计算器
    # Qwen/Qwen3-32B
    # Qwen/Qwen3-Embedding-0.6B
    # moonshotai/Kimi-K2-Instruct # 这个似乎不可用
    # deepseek-ai/DeepSeek-V3-0324
    """
    def __init__(self, model_name: str = "deepseek-ai/DeepSeek-V3-0324"):
        global _global_tokenizers
        if model_name not in _global_tokenizers:
            from modelscope import AutoTokenizer
            # 加载快速分词器
            _global_tokenizers[model_name] = AutoTokenizer.from_pretrained(model_name, use_fast=True, trust_remote_code=True)
        self.tokenizer = _global_tokenizers[model_name]

    def count_tokens(self, text: str) -> int:
        # 对文本进行编码并返回token数量
        tokens = self.tokenizer(text, return_tensors=None)
        # tokenizer返回字典，其中input_ids是token id列表
        return len(tokens.get('input_ids', []))


class OpenAITokenCalculator(TokenCalculator):
    """
    基于OpenAI tiktoken的token计算器，默认使用gpt-3.5-turbo编码
    """
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        import tiktoken
        self.model_name = model_name
        try:
            # 尝试获取模型专用的编码器
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # 回退到通用编码
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        # 对文本进行编码并返回token数量
        return len(self.encoding.encode(text))
# 测试下moonshotai/Kimi-K2-Instruct
if __name__ == "__main__":
    calculator = TransformerTokenCalculator(model_name="deepseek-ai/DeepSeek-V3-0324")
    text = "这是一个测试文本，用于计算token数量。"
    print(f"Token数量: {calculator.count_tokens(text)}")  # 输出token数量