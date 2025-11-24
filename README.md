# 📖 项目介绍

![HearSight logo](https://oss-liuchengtu.hudunsoft.com/userimg/33/3374fce0ebc0d82f093c6c7361b84fcc.png)

HearSight 是一个音视频内容智能分析工具。通过集成先进的语音识别、自然语言处理和大语言模型技术，HearSight 能够自动将视频和音频转化为结构化的文本内容，并在此基础上进行多维度的智能分析和交互。无论您是进行学术研究、内容创作还是知识管理，HearSight 都能帮助您深度挖掘音视频内容的价值。

[B站视频介绍](https://www.bilibili.com/video/BV1D5UgBYEtC/?vd_source=325d9b8b91626b0afd2ef63a99caf970)

<div style="text-align: center; margin: auto;">
    <iframe src="//player.bilibili.com/player.html?isOutside=true&aid=115602047899223&bvid=BV1D5UgBYEtC&cid=34218837346&p=1" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true"></iframe>
</div>


项目地址：<https://github.com/li-xiu-qi/HearSight>

## 🛠 技术架构

HearSight 采用现代化的微服务架构设计。后端基于 FastAPI 构建高性能 RESTful API，通过 PostgreSQL 实现数据的持久化和查询优化，通过 Celery 构建任务队列处理异步任务；前端采用 React 18 + TypeScript + Tailwind CSS 提供交互流畅的用户界面。整体支持 Docker 容器化部署，开箱即用。

![架构图](https://oss-liuchengtu.hudunsoft.com/userimg/b5/b54f2ca20885a98aa90ec0557b8354e1.png)

## ✨ 核心能力

![核心能力](https://oss-liuchengtu.hudunsoft.com/userimg/eb/eb8ce69e51ffee1798ab4419f391adab.png)

- 📹 集成式媒体导入：直接从哔哩哔哩获取内容，同时支持本地上传视频和音频文件，支持 MP4、AVI、MOV、MKV、MP3、WAV、M4A、AAC 等多种格式
- 🎯 精准语音转写：采用业界领先的 ASR 技术，支持热词识别和实时精确时间戳，自动分句并生成可交互式的文本档案
- 🧠 智能内容分析：基于大语言模型生成段落级和全文级的结构化摘要，支持持久化保存和迭代优化
- 💬 对话式内容理解：支持基于原文的深度问答交互，准确把握关键信息和核心观点
- 🖼️ 多模态信息展示：在问答和总结中融入视频关键帧，实现图文融合的高效表达（仅适用于视频内容）
- 🌐 多语言内容转换：支持自动翻译为多种语言，翻译结果完整保存，便于国际化场景使用

<!-- 效果展示 -->
## 🔧 效果展示

视频播放页展示：
![视频播放页展示](https://oss-liuchengtu.hudunsoft.com/userimg/27/27e3d807bc8e6a3abf5739eeb5effb27.png)

打开一个视频：

![打开一个视频](https://oss-liuchengtu.hudunsoft.com/userimg/8d/8daf5b438a9de50fd4425ee1518536a9.png)

打开视频后的文稿效果展示：

![打开视频后的文稿效果展示](https://oss-liuchengtu.hudunsoft.com/userimg/f5/f548ca996e1b001e371df9bca74fc60a.png)

视频总结的展示：

![视频总结的展示](https://oss-liuchengtu.hudunsoft.com/userimg/de/defdd1d7dd03e7b34f34232895455dd9.png)
![视频总结的放大图片展示](https://oss-liuchengtu.hudunsoft.com/userimg/0f/0f4df03f82e2250bc3c6f77d87514f8c.png)

与视频之间的智能对话：

![与视频之间的智能对话](https://oss-liuchengtu.hudunsoft.com/userimg/73/73c98a266a46f1b4524772227c89f23a.png)

![与视频之间的智能对话](https://oss-liuchengtu.hudunsoft.com/userimg/4b/4bd189e43bc033aa1b3e3abc14f9bac6.png)

![图文模式对话图片放大展示](https://oss-liuchengtu.hudunsoft.com/userimg/45/45b084440a50e098229d8c827ab5f01f.png)

## 📂 项目结构

详细的项目结构说明请参考 [项目结构](docs/项目结构.md)。

## 📡 API 文档

API 接口文档请参考 [API 文档导航](docs/api_文档导航.md)。

## 🚀 快速开始

详细的快速开始指南请参考 [快速开始](docs/快速开始.md)。

## 🎯 适用场景

学术研究：快速整理讲座音频或视频，建立参考文献档案库。教育培训：自动生成教学讲义和习题解析。内容创作：批量处理视频脚本和文案素材。企业培训：构建结构化的内部知识库与学习平台。客户服务：分析客服录音提取关键问题与解决方案。市场研究：监测竞品视频内容并自动生成分析报告。

## 🔧 功能详解

### 1. 多源媒体导入

集成哔哩哔哩接口可直接获取视频（含登录内容），同时支持本地上传多种格式的音视频文件。系统自动处理文件管理和元数据存储，用户无需手动处理繁琐的文件操作。

### 2. 精准语音识别与时间戳分句

采用行业前沿的 ASR 模型，支持热词识别优化垂直领域准确度。系统自动按句义分割，每个分句精确对应音频时间戳，支持点击即跳转到音视频位置，打破传统文案的线性查看方式。

### 3. 分层级摘要生成与版本管理

集成大语言模型生成分层级摘要，既能快速获取段落关键信息，也能完整掌握全文内容脉络。摘要自动入库，支持查看历史版本与迭代对比，支持强制重新生成自动覆盖，让内容分析全过程可追溯。

### 4. 多语言翻译与存储

支持一键翻译为多种目标语言，后台异步处理不阻塞主流程，支持实时查看翻译进度。翻译结果完整持久化，多语言内容共存于一个项目中，轻松管理国际化内容。

### 5. 深度问答交互

基于原始转写内容进行上下文感知的问答。支持多轮追问与对话历史完整保留，系统能准确把握内容脉络，给出针对性的分析答案。

### 6. 图文融合呈现

自动关联视频关键帧到摘要和问答结果中（仅适用于视频内容）。用户可点击查看大图，实现图文结合的直观表达，让复杂概念更容易理解。

## 🤝 参与贡献

HearSight 是一个开源项目，我们欢迎来自社区的改进和贡献。无论是功能增强、bug 修复还是文档改进，都可以通过提交 Pull Request 的方式参与。如果有好的想法或发现问题，也可以直接提交 Issue。

## 📝 开源许可

本项目采用 Apache-2.0 License 开源许可证。详见 LICENSE 文件。
