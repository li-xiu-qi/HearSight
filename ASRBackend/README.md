# ASR Backend README

## 项目概述

ASRBackend 是 HearSight 项目的语音识别后端，支持两种运行模式：

- **本地模式**: 使用 FunASR 的 Paraformer 模型，完全离线运行
- **云端模式**: 使用阿里云 DashScope API，轻量级部署

## 功能特性

- 音频转文本识别（中英文）
- 说话人分离
- 自动添加标点
- 句子智能分段和合并
- 健康检查接口
- 双模式支持（本地/云端）
- **云端模式文件上传**：自动上传到 Supabase 存储后进行识别

## 快速开始

### 环境准备

Python 3.10+

### 创建虚拟环境

```bash
# 使用 conda（推荐）
conda create -n asr-backend python=3.10
conda activate asr-backend

# 或使用 venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate (Windows)
```

### 选择运行模式

#### 云端模式（默认，轻量级）

```bash
# 安装云端版本依赖
pip install -r requirements-cloud.txt

# 设置 API Key
export DASHSCOPE_API_KEY="your-api-key-here"  # Linux/Mac
# 或 set DASHSCOPE_API_KEY=your-api-key-here  # Windows

# 启动服务
python main.py
```

#### 本地模式（完整功能）

```bash
# 安装本地版本依赖
pip install -r requirements-local.txt

# 安装 PyTorch（根据硬件选择）
# GPU 版本 (CUDA 12.1):
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cu121

# CPU 版本:
pip install torch==2.1.0

# 启动服务
ASR_MODE=local python main.py
```

### Docker 部署

#### 云端版本（推荐）

```bash
# 构建
docker build -f Dockerfile.cloud -t asr-backend:cloud .

# 运行
docker run -d -p 8003:8003 \
  -e DASHSCOPE_API_KEY="your-api-key" \
  asr-backend:cloud
```

#### 本地版本

```bash
# 构建
docker build -f Dockerfile.local -t asr-backend:local .

# 运行
docker run -d -p 8003:8003 \
  -e ASR_MODE=local \
  asr-backend:local
```

## API 使用

### 转录音频

```bash
# 云端模式 - 文件上传（自动上传到 Supabase）
curl -X POST http://localhost:8003/asr/transcribe \
  -F "file=@audio.wav"

# 云端模式 - URL 转录
curl -X POST http://localhost:8003/asr/transcribe \
  -F "url=https://example.com/audio.wav"

# 本地模式 - 文件上传
curl -X POST http://localhost:8003/asr/transcribe \
  -F "file=@audio.wav"
```

### 获取服务信息

```bash
curl http://localhost:8003/asr/info
```

### 健康检查

```bash
curl http://localhost:8003/health
```

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `ASR_MODE` | 运行模式 | `cloud` | `local` |
| `DASHSCOPE_API_KEY` | 云端 API Key | - | `sk-xxx` |
| `SUPABASE_URL` | Supabase 项目 URL | - | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Supabase API Key | - | `eyJ0eXAiOiJKV1Qi...` |
| `SUPABASE_BUCKET_NAME` | 存储桶名称 | `test-public` | `audio-storage` |
| `SUPABASE_FOLDER_NAME` | 上传文件夹 | `asr` | `uploads` |
| `DEBUG` | 调试模式 | `true` | `false` |
| `PORT` | 服务端口 | `8003` | `8080` |

### 配置文件

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
# 编辑 .env 文件
```

## 开发说明

### 项目结构

ASRBackend/
├── asr_functions/     # ASR 功能模块
├── routers/          # API 路由
├── services/         # 业务逻辑服务
├── supabase_utils/   # Supabase 文件上传工具
├── config.py         # 配置管理
├── providers.py      # 提供者工厂
├── main.py           # 应用入口
└── requirements-*.txt # 依赖文件

## 故障排除

### 配置缺失错误

#### Supabase 配置缺失（云端模式文件上传）

**错误现象**：

- 云端模式下上传文件时返回 `"error": "Supabase配置缺失"`

**解决方案**：

1. 确保已设置以下环境变量：

   ```bash
   export SUPABASE_URL="https://your-project.supabase.co"
   export SUPABASE_KEY="your-anon-key"
   ```

2. 或在 `.env` 文件中配置相应变量

3. 重启服务

**降级方案**：

- 使用 URL 方式上传（先手动上传文件到其他存储服务，获取公开 URL）
- 切换到本地模式（如果有本地模型）

#### DashScope API Key 缺失（云端模式）

**错误现象**：

- 云端模式下所有请求返回 `"error": "ASR服务异常"`

**解决方案**：

1. 设置有效的 API Key：

   ```bash
   export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxx"
   ```

2. 从 [DashScope 控制台](https://dashscope.console.aliyun.com/) 获取 API Key

**降级方案**：

- 切换到本地模式（需要本地模型）

### 本地模式错误

#### 模型文件缺失

**错误现象**：

- 本地模式启动失败
- 导入时出现模型下载错误

**解决方案**：

1. 确保网络连接正常（模型会自动下载）
2. 检查磁盘空间（FunASR 模型约 1-2GB）
3. 手动下载模型文件到缓存目录

**降级方案**：

- 切换到云端模式（需要 API Key）

#### GPU/CPU 兼容性问题

**错误现象**：

- 本地模式推理失败
- CUDA 相关错误

**解决方案**：

1. 检查 PyTorch 版本是否匹配硬件
2. 使用 CPU 版本：`pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu`

**降级方案**：

- 切换到云端模式

### 运行时错误

#### 文件上传失败

**错误现象**：

- 文件上传到 Supabase 失败
- 返回 `"error": "文件上传失败: xxx"`

**可能原因**：

- Supabase 服务不可用
- 存储桶权限不足
- 网络连接问题

**解决方案**：

1. 检查 Supabase 服务状态
2. 验证存储桶权限设置
3. 检查网络连接

**降级方案**：

- 使用 URL 方式（先上传到其他存储服务）

#### 音频格式不支持

**错误现象**：

- 返回 `"error": "不支持的文件格式"`

**支持格式**：

- WAV, MP3, M4A, FLAC, OGG

**解决方案**：

- 转换音频格式后再上传
- 使用支持的格式录制音频

### 性能优化

#### 云端模式优化

- 文件上传前先压缩音频（减小文件大小）
- 使用稳定的网络连接
- 避免并发大量请求

#### 本地模式优化

- 使用 GPU 加速（如果可用）
- 预加载模型（减少首次推理时间）
- 合理设置并发数

**Linux (无 CUDA):**

```bash
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### 启动服务

```bash
python main.py
```

服务默认运行在 `http://localhost:8003`

## API 接口

### GET /health

健康检查接口

返回：

```json
{
  "status": "healthy",
  "service": "ASR Backend"
}
```

## 文档导航

- [架构概述](docs/ASBBackend_架构概述.md) - 项目结构和功能特性
- [快速开始指南](docs/ASRBackend_快速开始指南.md) - 详细的安装和启动步骤
- [API 接口文档](docs/ASRBackend_API_接口文档.md) - 接口使用说明
- [配置指南](docs/ASRBackend_配置指南.md) - 配置项说明
- [Docker 部署指南](docs/ASRBackend_Docker_部署指南.md) - Docker 部署方法
