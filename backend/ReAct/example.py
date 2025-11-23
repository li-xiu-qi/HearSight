"""ReAct 示例代码

使用 config.py 中的配置来测试 ReAct 代理。
"""

import asyncio
import os
import subprocess
import sys

# 添加项目根目录到路径，以便导入
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import settings
from ReAct import BaseAgent


async def main():
    """主函数，使用 MCP 工具服务器进行推理。"""

    # 从 config 获取配置
    api_key = settings.llm_provider_api_key
    api_base = settings.llm_provider_base_url or "https://api.openai.com/v1"
    model = settings.llm_model or "gpt-3.5-turbo"

    if not api_key:
        print("请在 config.py 或环境变量中设置 llm_provider_api_key。")
        return

    print("启动本地工具 MCP 服务器...")

    # 启动工具服务器（在后台运行）
    import subprocess
    import sys
    import os

    server_script = os.path.join(os.path.dirname(__file__), "tools_server.py")
    server_process = subprocess.Popen([sys.executable, server_script])

    # 等待服务器启动
    await asyncio.sleep(2)

    try:
        print("创建 ReAct 代理...")

        # 创建 BaseAgent，连接到本地 MCP 服务器
        agent = BaseAgent(
            openai_api_key=api_key,
            openai_api_base=api_base,
            openai_api_model=model,
            tools_backend_url="http://localhost:8001",  # 本地 MCP 服务器地址
            config_path=None,
        )

        # 用户问题
        question = "计算 2 + 3 的结果。"

        print(f"执行推理: {question}")

        # 执行推理
        result = await agent.react_loop.run(question, allowed_tools=["calculator"])

        print(f"最终答案: {result.final_answer}")
        print("推理轨迹:")
        for step in result.trace:
            print(f"  步骤 {step.step}: {step.thought}")
            if step.action:
                print(f"    动作: {step.action}")
            if step.action_input:
                print(f"    输入: {step.action_input}")
            if step.observation:
                print(f"    观察: {step.observation}")

    finally:
        # 停止服务器
        print("停止工具服务器...")
        server_process.terminate()
        server_process.wait()

    print("测试完成。")


if __name__ == "__main__":
    asyncio.run(main())