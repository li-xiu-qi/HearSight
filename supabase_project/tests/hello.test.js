import { describe, expect, it } from "vitest";

const supabaseUrl = "http://localhost:8000";
const functionsBase = `${supabaseUrl}/functions/v1`;

describe("hello 函数测试", () => {
    it("应该返回成功响应", async () => {
        try {
            const response = await fetch(`${functionsBase}/hello`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                }
            });

            console.log("hello 响应状态:", response.status);
            const text = await response.text();
            console.log("hello 响应体:", text);

            expect(response.status).toBe(200);
        } catch (error) {
            console.error("hello 请求失败:", error.message);
            throw error;
        }
    }, 15000);

    it("应该处理认证头", async () => {
        const response = await fetch(`${functionsBase}/hello`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer test_token"
            }
        });

        console.log("带认证头的hello响应:", response.status);
        expect(response.ok).toBe(true);
    });
});
