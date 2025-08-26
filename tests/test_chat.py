# 任意位置，如 backend/xxx.py
import sys
from pathlib import Path

# 将项目根目录加入 sys.path（tests -> backend -> HearSight）
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.chat_utils import chat, chat_text

# 简单问答
reply = chat_text("用一句话介绍你自己", temperature=0.3)
print(reply)

# 标准 messages 结构
msgs = [
    {"role": "system", "content": "你是一个有帮助的助手"},
    {"role": "user", "content": "给我一个 Python 生成器的例子"},
]
reply2 = chat(msgs, temperature=0.2)
print(reply2)
