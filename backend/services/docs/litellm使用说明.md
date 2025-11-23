# LiteLLM 使用说明

## 概述

LiteLLM 是一个统一的 LLM API 客户端，支持多种大语言模型提供商。本项目使用 LiteLLM Router 来调用各种 LLM 服务，支持速率限制和负载均衡。

## 项目中的使用

### 配置

在 `backend/.env` 中配置：

```env
LLM_PROVIDER=openai
LLM_MODEL=deepseek-ai/DeepSeek-V3.2-Exp
LLM_PROVIDER_BASE_URL=https://api.siliconflow.cn/v1
LLM_PROVIDER_API_KEY=your-api-key
LLM_TPM=80000
LLM_RPM=1000
```

### 示例代码

参考 `litellm_example.py` 文件中的完整示例。

#### 基本调用

```python
from litellm import Router
from backend.config import settings

# 构建模型参数
model = f"{settings.llm_provider}/{settings.llm_model}"
api_key = settings.llm_provider_api_key
base_url = settings.llm_provider_base_url
tpm = settings.llm_tpm
rpm = settings.llm_rpm

# 配置模型列表
model_list = [{
    "model_name": settings.llm_model,
    "litellm_params": {
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
        "tpm": tpm,
        "rpm": rpm,
    }
}]

# 创建 Router
router = Router(model_list=model_list)

# 调用
messages = [{"role": "user", "content": "请总结这个视频的内容"}]
response = router.completion(
    model=settings.llm_model,
    messages=messages,
)

print(response.choices[0].message.content)
```

#### 流式调用

```python
response = router.completion(
    model=settings.llm_model,
    messages=messages,
    stream=True,
)

print("流式响应:")
for chunk in response:
    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)
print("\n流式完成")
```

#### Embedding 调用

```python
# 异步 embedding 调用
import asyncio

async def embedding_example():
    # 构建模型列表（包含 embedding 模型）
    model_list = [
        {
            "model_name": settings.embedding_model,
            "litellm_params": {
                "model": settings.embedding_model,
                "api_key": settings.embedding_provider_api_key,
                "api_base": settings.embedding_provider_base_url,
                "custom_llm_provider": settings.embedding_provider,
            },
            "tpm": settings.embedding_tpm,
            "rpm": settings.embedding_rpm,
        },
    ]

    router = Router(model_list=model_list)

    input_text = "请总结这个视频的内容"

    response = await router.aembedding(
        model=settings.embedding_model,
        input=input_text
    )

    # 获取向量
    embedding_vector = response.data[0]['embedding']
    print(f"向量维度: {len(embedding_vector)}")
    print(f"前5个值: {embedding_vector[:5]}")

# 运行异步函数
asyncio.run(embedding_example())
```

参考 `embedding_litellm_example.py` 文件中的完整示例。

## 关键点

1. **模型命名**: 使用 `{provider}/{model_name}` 格式，如 `openai/deepseek-ai/DeepSeek-V3.2-Exp`
2. **Router 配置**: 在 `litellm_params` 中设置 `tpm` 和 `rpm` 进行速率限制
3. **调用方式**: 使用 `router.completion()` 而不是直接 `litellm.completion()`
4. **流式处理**: 正确迭代响应流，检查 `chunk.choices[0].delta.content`
