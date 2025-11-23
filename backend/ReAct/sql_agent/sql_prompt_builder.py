"""SQL Agent 提示词生成器"""

from dataclasses import dataclass
from textwrap import dedent
from typing import Sequence


@dataclass
class TableConfig:
    """表配置结构体"""

    language: str
    table_structure: str
    business_background: str
    notes: str
    examples: str

    def to_str(self) -> str:
        """转换为字符串"""
        return f"""{self.language}

{self.table_structure}

{self.business_background}

{self.notes}

{self.examples}"""


# Solar 表配置（包含表格结构和业务背景）
SOLAR_TABLE_CONFIG = TableConfig(
    language="查询语言为PostgreSQL方言。",
    table_structure="""
表：solar (
date DATETIME -- 时间（格式示例：2021/1/11 0:00）,
pressure DOUBLE -- 气压,
humidity DOUBLE -- 相对湿度,
cloudiness DOUBLE -- 云层覆盖程度,
temperature DOUBLE -- 气温,
windSpeed DOUBLE -- 风速,
irradiance DOUBLE -- 太阳辐照度,
realPower DOUBLE -- 真实发电功率（目标变量）,
theoryPower INT -- 理论发电功率
)
""".strip(),
    business_background="业务背景：预测 realPower 列，使用前序时刻的辐照强度及气象参数作为特征。",
    notes='注意：列名大小写敏感，请在 SQL 查询中使用双引号引用列名，例如 "realPower"。',
    examples='示例查询：SELECT date, "realPower" FROM solar ORDER BY date DESC LIMIT 5;',
)


def build_sql_agent_system_prompt(
    action_names: Sequence[str],
    tool_description: str = "",
) -> str:
    """
    构建 SQL Agent 系统提示词

    参数:
        action_names: 可用的动作名称列表（如 ['generate_sql', 'execute_query', 'finish']）
        tool_description: 工具描述文本

    返回:
        系统提示词文本
    """
    allowed_list = " | ".join(action_names)
    prompt = f"""
    你是擅长 SQL 的 ReAct 智能体。请严格按以下格式输出：

    Thought: （你的思考过程）
    Action: 动作名称（仅支持 {allowed_list}）
    Action Input: 动作的输入（JSON 格式）
    Observation: 动作返回的结果（由系统填充）

    {tool_description}

    # SQL 查询流程

    当需要查询数据库时，请按以下步骤思考：
    1. 理解用户问题和表格结构
    2. 生成合适的 SQL 查询语句
    3. 调用 execute_sql_tool 执行查询

    表格配置和业务背景：
    {SOLAR_TABLE_CONFIG.to_str()}

    SQL 生成规则：
    - 禁止使用 SELECT * 查询所有列，必须明确指定需要的列名
    - 禁止查询整个表格的所有内容，每次查询最多返回5行数据
    - 必须使用 LIMIT 5 或等效语法限制结果数量
    - 如果需要查看数据样本，使用 ORDER BY 和 LIMIT 5 获取前5条记录

    # 例子

    Thought: 用户问今天发电量是多少，我需要查询 solar 表中 date 为今天的 realPower 字段。
    Action: execute_sql_tool
    Action Input: {{"sql": "SELECT \"realPower\" FROM solar WHERE DATE(date) = CURRENT_DATE LIMIT 5"}}

    当你已经拿到足够信息并且可以给出最终答案时，必须输出：

    Thought: （这里说明你已经可以回答问题了）
    Final Answer: （这里直接用自然语言回答用户）

    # 注意：
    - 只能输出 "Thought:"、"Action:"、"Action Input:"、"Final Answer:" 这些前缀。
    - 严格按照格式，不要输出任何多余内容。
    - 可重复 Thought-Action-Observation，直到你能回答用户问题时执行 finish。
    """
    return dedent(prompt).strip()
