import os
import sys

# 确保将项目 backend 目录加入到导入路径，便于从 tests 目录直接运行
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from download_video.download_bilibili import download_bilibili

example_url = "https://www.bilibili.com/video/BV1pm8dzXEpA?spm_id_from=333.1007.tianma.2-3-6.click"  # 示例占位
sess = os.getenv("BILI_SESSDATA", "")
paths = download_bilibili(example_url, out_dir="downloads", playlist=False, sessdata=sess)
print("Saved files:")
for p in paths:
    print(p)