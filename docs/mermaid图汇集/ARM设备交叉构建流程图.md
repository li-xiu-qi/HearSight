# ARM设备交叉构建流程图

```mermaid
flowchart TD
    A[启用Docker Buildx] --> B[检查Dockerfile兼容性]
    B --> C[构建多架构镜像]
    C --> D[保存镜像为文件]
    D --> E[传输到ARM设备]
    E --> F[加载并运行镜像]
```
