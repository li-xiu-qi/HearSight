"""
基于 ReAct 范式的 SQL Agent

特性：
- 支持 ReAct 多步推理
- 支持结构化输出（trace + 最终答案）
- 支持流式响应
- 模块化设计，易于扩展
"""

import os

from config import settings

from ..ReAct.base_agent import BaseAgent
from .sql_prompt_builder import build_sql_agent_system_prompt


class SQLAgent(BaseAgent):
    """
    基于 ReAct 范式的 SQL Agent

    支持：
    1. 自然语言转 SQL
    2. SQL 查询执行
    3. 多步推理
    4. 结构化输出（trace 记录）
    5. 流式响应
    """

    def __init__(
        self,
        openai_api_key: str,
        openai_api_base: str,
        openai_api_model: str,
        tools_backend_url: str,
    ):
        # 构建配置文件路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "sql_agent_tool_limit.json")

        super().__init__(
            openai_api_key=openai_api_key,
            openai_api_base=openai_api_base,
            openai_api_model=openai_api_model,
            tools_backend_url=tools_backend_url,
            config_path=config_path,
            prompt_builder=build_sql_agent_system_prompt,
            extra_headers={"DashScope-Plugin": "optional"},
        )


# ===== 全局实例 =====
sql_agent = SQLAgent(
    openai_api_key=settings.openai_api_key,
    openai_api_base=settings.openai_api_base,
    openai_api_model=settings.openai_api_model,
    tools_backend_url=settings.tools_backend_url,
)
