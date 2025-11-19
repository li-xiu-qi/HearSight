# -*- coding: utf-8 -*-
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import json
from backend.audio2text.asr_sentence_segments import process

if __name__ == "__main__":
    # audio_path = r"C:\Users\ke\Documents\projects\python_projects\HearSight\backend\tests\datas\大语言模型进化论：从“听懂指令”到“学会思考”，AI如何与人类对齐？.m4a"
    audio_path = r"C:\Users\ke\Documents\projects\python_projects\HearSight\backend\tests\datas\test.mp4"
    out = process(audio_path)
    print(json.dumps(out, ensure_ascii=False, indent=2))