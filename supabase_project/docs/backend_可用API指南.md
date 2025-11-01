# 可用API指南

Backend 通过 Supabase Edge Functions 提供以下 API 端点。

## API 端点

### GET /functions/v1/hello

健康检查端点，验证服务运行状态。

**响应：**

```json
{"message":"Hello from hello!"}
```

**示例：**

```bash
curl http://localhost:8000/functions/v1/hello
```

## 认证说明

需要认证的 API 使用 Supabase Auth 验证。流程：

1. 通过 Supabase Auth 获取 JWT token
2. 在请求头中添加 `Authorization: Bearer token`
3. 服务端验证 token 有效性

## 错误处理

- **401 Unauthorized**：认证失败或 token 无效
- **400 Bad Request**：请求体格式错误
- **500 Internal Server Error**：服务端错误

## 相关文档

- [快速开始](backend_快速开始指南.md)
- [架构概述](backend_架构概述.md)
- [配置指南](backend_配置指南.md)
