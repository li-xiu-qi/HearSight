# ARM设备直接构建流程图

```mermaid
flowchart TD
    A[在ARM设备上安装Docker] --> B[传输项目代码]
    B --> C[配置环境变量]
    C --> D[运行docker-compose build]
    D --> E[运行docker-compose up]
```
