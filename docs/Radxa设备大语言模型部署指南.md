
# Radxa设备大语言模型部署指南

## 概述

本文档介绍在Radxa设备上部署大型语言模型（LLM）的工具和方法，主要包括Llama.cpp和Ollama。

## Llama.cpp

Llama.cpp的主要目标是在各种硬件（本地和云端）上实现LLM推理，只需最少的设置，同时提供最先进的性能。

### 量化格式对比

以下是不同的量化格式及其性能表现（基于Llama-3-8B模型）：

```text
2 或 Q4_0    : 4.34GB, +0.4685 困惑度 @ Llama-3-8B
3 或 Q4_1    : 4.78GB, +0.4511 困惑度 @ Llama-3-8B
8 或 Q5_0    : 5.21GB, +0.1316 困惑度 @ Llama-3-8B
9 或 Q5_1    : 5.65GB, +0.1062 困惑度 @ Llama-3-8B
19 或 IQ2_XXS : 2.06 bpw 量化
20 或 IQ2_XS  : 2.31 bpw 量化
28 或 IQ2_S   : 2.5  bpw 量化
29 或 IQ2_M   : 2.7  bpw 量化
24 或 IQ1_S   : 1.56 bpw 量化
31 或 IQ1_M   : 1.75 bpw 量化
36 或 TQ1_0   : 1.69 bpw 三值化
37 或 TQ2_0   : 2.06 bpw 三值化
10 或 Q2_K    : 2.96GB, +3.5199 困惑度 @ Llama-3-8B
21 或 Q2_K_S  : 2.96GB, +3.1836 困惑度 @ Llama-3-8B
23 或 IQ3_XXS : 3.06 bpw 量化
26 或 IQ3_S   : 3.44 bpw 量化
27 或 IQ3_M   : 3.66 bpw 量化混合
12 或 Q3_K    : Q3_K_M的别名
22 或 IQ3_XS  : 3.3 bpw 量化
11 或 Q3_K_S  : 3.41GB, +1.6321 困惑度 @ Llama-3-8B
12 或 Q3_K_M  : 3.74GB, +0.6569 困惑度 @ Llama-3-8B
13 或 Q3_K_L  : 4.03GB, +0.5562 困惑度 @ Llama-3-8B
25 或 IQ4_NL  : 4.50 bpw 非线性量化
30 或 IQ4_XS  : 4.25 bpw 非线性量化
15 或 Q4_K    : Q4_K_M的别名
14 或 Q4_K_S  : 4.37GB, +0.2689 困惑度 @ Llama-3-8B
15 或 Q4_K_M  : 4.58GB, +0.1754 困惑度 @ Llama-3-8B
17 或 Q5_K    : Q5_K_M的别名
16 或 Q5_K_S  : 5.21GB, +0.1049 困惑度 @ Llama-3-8B
17 或 Q5_K_M  : 5.33GB, +0.0569 困惑度 @ Llama-3-8B
18 或 Q6_K    : 6.14GB, +0.0217 困惑度 @ Llama-3-8B
7 或 Q8_0    : 7.96GB, +0.0026 困惑度 @ Llama-3-8B
1 或 F16     : 14.00GB, +0.0020 困惑度 @ Mistral-7B
32 或 BF16    : 14.00GB, -0.0050 困惑度 @ Mistral-7B
0 或 F32     : 26.00GB @ 7B
        COPY    : 仅复制张量，不量化
```

### 实际使用示例

#### 对话示例

```text
> 你好，你是谁
<think>

</think>

你好！我是DeepSeek-R1，由DeepSeek创建的人工智能助手。我随时为您服务，很乐意协助您解决任何疑问或任务。
```

#### 性能基准测试

在Radxa Orion O6上进行性能测试：

```bash
radxa@orion-o6:~/llama.cpp/build/bin$ ./llama-bench -m ~/DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf -t 8
| 模型                          |       大小 |     参数量 | 后端    | 线程数 |          测试 |                  速度 |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | ------------: | -------------------: |
| qwen2 1.5B Q4_K - Medium       |   1.04 GB |     1.78 B | CPU        |       8 |         pp512 |         64.60 ± 0.27 |
| qwen2 1.5B Q4_K - Medium       |   1.04 GB |     1.78 B | CPU        |       8 |         tg128 |         36.29 ± 0.16 |
```

测试结果显示，在8线程配置下，预填充速度达到64.60 tokens/秒，生成速度达到36.29 tokens/秒。

## Ollama

Ollama是一个在本地运行和管理大型语言模型（LLM）的工具。它使您能够轻松地在本地设备上拉取、运行和管理各种AI模型（如LLaMA、Mistral和Gemma），而无需复杂的环境配置。

### 安装Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

关于本地构建方法，请参考[官方文档](https://github.com/ollama/ollama/blob/main/docs/development.md)。

### 使用方法

#### 拉取模型

此命令从互联网下载模型文件。

```bash
ollama pull deepseek-r1:1.5b
```

#### 运行模型

此命令直接运行模型。如果模型未在本地缓存，它会在运行前自动下载。

```bash
ollama run deepseek-r1:1.5b
```

#### 显示模型信息

```bash
ollama show deepseek-r1:1.5b
```

#### 列出计算机上的模型

```bash
ollama list
```

#### 列出当前已加载的模型

```bash
ollama ps
```

#### 停止当前正在运行的模型

```bash
ollama stop deepseek-r1:1.5b
```

#### 删除模型

```bash
ollama rm deepseek-r1:1.5b
```

## 参考

- Llama.cpp官方文档：<https://github.com/ggml-org/llama.cpp>
- 使用Llama.cpp在Radxa上运行LLM：<https://docs.radxa.com/en/orion/o6/app-development/artificial-intelligence/llama_cpp>
- Ollama官方文档：<https://github.com/ollama/ollama>
- 使用Ollama在Radxa上运行LLM：<https://docs.radxa.com/en/orion/o6/app-development/artificial-intelligence/ollama>
