# 依赖管理指南

Backend 依赖通过 Deno URL 导入、Docker 镜像和 Node.js npm 三种方式管理。

## Deno 依赖（Edge Functions）

Edge Functions 使用 Deno 运行时，通过 URL 导入管理依赖，无需传统包管理文件。

### 标准库依赖

```typescript
// HTTP 服务器
import { serve } from "https://deno.land/std@0.177.1/http/server.ts"

// JSON 处理
import { parse, stringify } from "https://deno.land/std@0.177.1/encoding/json.ts"

// UUID 生成
import { v4 } from "https://deno.land/std@0.177.1/uuid/mod.ts"
```

### 第三方模块

```typescript
// JWT 处理
import * as jose from "https://deno.land/x/jose@v4.14.4/index.ts"

// Supabase 客户端
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"
```

### import_map.json 配置

项目根目录的 `import_map.json` 定义导入别名：

```json
{
  "imports": {
    "std/": "https://deno.land/std@0.177.1/",
    "jose": "https://deno.land/x/jose@v4.14.4/index.ts"
  }
}
```

使用别名简化导入：

```typescript
import { serve } from "std/http/server.ts"
import * as jose from "jose"
```

### 版本管理

- **固定版本**：在 URL 中使用具体版本号，避免兼容性问题
- **定期检查**：定期检查上游依赖更新
- **本地测试**：更新前在本地充分测试

## Docker 依赖

### Supabase 镜像

```yaml
services:
  db:
    image: supabase/postgres:15.1.0.147
  kong:
    image: supabase/kong:0.47.2
  studio:
    image: supabase/studio:latest
```

## 测试框架依赖（Node.js）

Backend 的自动化测试使用 Node.js + Vitest。

### 安装依赖

```bash
cd backend/tests
npm install
```

### 主要依赖

```json
{
  "devDependencies": {
    "vitest": "latest",
    "node-fetch": "latest"
  }
}
```

### 依赖更新

```bash
npm update
```

## 相关文档

- [快速开始](backend_快速开始指南.md)
- [架构概述](backend_架构概述.md)
- [Docker 部署指南](backend_Docker_部署指南.md)
