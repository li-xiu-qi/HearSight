import json
import requests
from dotenv import load_dotenv
import os
import subprocess

load_dotenv()



token = os.getenv("OPENAI_API_KEY")

# 使用requests库发送POST请求到SiliconFlow API进行音频转录
url = "https://api.siliconflow.cn/v1/audio/transcriptions"
headers = {
    "Authorization": f"Bearer {token}"
}
wav_path = r"C:\Users\ke\Documents\projects\python_projects\HearSight\tests\converted_audio.wav"


files = {
    "file": open(wav_path, "rb")
}
data = {
    # "model": "FunAudioLLM/SenseVoiceSmall"
    "model": "TeleAI/TeleSpeechASR"
}

response = requests.post(url, headers=headers, files=files, data=data)

print(response.json())
# 写入json文件里面
with open("output.json", "w") as f:
    json.dump(response.json(), f)