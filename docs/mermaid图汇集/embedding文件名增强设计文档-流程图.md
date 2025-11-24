# embedding文件名增强设计文档 - 流程图

```mermaid
graph TD
    A[接收segments和metadata] --> B[分组为chunks]
    B --> C[获取文件名]
    C --> D[生成增强chunk_text]
    D --> E[计算embedding]
    E --> F[存储到ChromaDB]
```
