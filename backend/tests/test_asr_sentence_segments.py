# -*- coding: utf-8 -*-
import os, sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "example_tests"))

import json
from asr_sentence_segments import process

if __name__ == "__main__":
    # audio_path = r"C:\Users\ke\Documents\projects\python_projects\HearSight\backend\tests\datas\大语言模型进化论：从"听懂指令"到"学会思考"，AI如何与人类对齐？.m4a"
    audio_path = r"C:\Users\ke\Documents\projects\python_projects\HearSight\backend\tests\datas\test.mp4"
    out = process(audio_path)
    print(json.dumps(out, ensure_ascii=False, indent=2))