import json
import requests
from dotenv import load_dotenv
import os
import subprocess

load_dotenv()

def convert_video_to_wav(input_path, output_path):
    """
    使用ffmpeg将视频转换为WAV音频格式。
    """
    command = [
        "ffmpeg",
        "-i", input_path,
        "-vn",  # 移除视频流
        "-acodec", "pcm_s16le",  # 使用PCM编码
        output_path
    ]
    subprocess.run(command, check=True)

token = os.getenv("OPENAI_API_KEY")

# 使用requests库发送POST请求到SiliconFlow API进行音频转录
url = "https://api.siliconflow.cn/v1/audio/transcriptions"
headers = {
    "Authorization": f"Bearer {token}"
}
video_path = r"C:\Users\ke\Documents\projects\python_projects\HearSight\app_datas\download_videos\【从零开始学OB】—— 百变强大的Obsidian 社区主题：Blue Topaz.mp4"
wav_path = r"C:\Users\ke\Documents\projects\python_projects\HearSight\tests\converted_audio.wav"

# 转换视频为WAV
convert_video_to_wav(video_path, wav_path)

files = {
    "file": open(wav_path, "rb")
}
data = {
    "model": "FunAudioLLM/SenseVoiceSmall"
}

response = requests.post(url, headers=headers, files=files, data=data)

print(response.json())
# 写入json文件里面
with open("output.json", "w") as f:
    json.dump(response.json(), f)