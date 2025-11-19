import os
import sys
import json

# 确保将项目 backend 目录加入到导入路径，便于从 tests 目录直接运行
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from audio2text.audio2text import audio_to_text

audio_path = r"C:\Users\ke\Documents\projects\python_projects\HearSight\backend\tests\datas\大语言模型进化论：从“听懂指令”到“学会思考”，AI如何与人类对齐？.m4a"
text, segments = audio_to_text(audio_path, return_segments=True)
print(text)
# 如需保存解析结果，可自行取消下面注释
output_dir = "results"
os.makedirs(output_dir, exist_ok=True)
with open(os.path.join(output_dir, 'test_audio2text.json'), 'w', encoding='utf-8') as f:
    json.dump(segments, f, ensure_ascii=False, indent=2)
