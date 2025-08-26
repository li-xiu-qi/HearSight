import os
import sys
import json

# 确保将项目 backend 目录加入到导入路径，便于从 tests 目录直接运行
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from audio2text.paraformer_a2t import paraformer_audio_to_text

# 使用与现有测试一致的数据路径（可按需修改为你的绝对路径）
audio_path = r"C:\Users\ke\Documents\projects\python_projects\HearSight\backend\tests\datas\大语言模型进化论：从“听懂指令”到“学会思考”，AI如何与人类对齐？.m4a"

# 直接转写，拿到文本、段级时间戳与按秒聚合
res = paraformer_audio_to_text(audio_path, return_segments=True)

if isinstance(res, tuple) and len(res) == 3:
    text, segments, per_second = res
else:
    # 兜底：老版本只返回文本
    text, segments, per_second = str(res), [], {}

print(text)

# 如需保存解析结果
output_dir = "results"
os.makedirs(output_dir, exist_ok=True)

with open(os.path.join(output_dir, 'test_paraformer_a2t_segments.json'), 'w', encoding='utf-8') as f:
    json.dump(segments, f, ensure_ascii=False, indent=2)

with open(os.path.join(output_dir, 'test_paraformer_a2t_per_second.json'), 'w', encoding='utf-8') as f:
    json.dump(per_second, f, ensure_ascii=False, indent=2)
