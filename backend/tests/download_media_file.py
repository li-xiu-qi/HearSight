import yt_dlp
import sys
import os
import argparse

def download_media(url, output_dir='downloads', list_formats=False):
    """
    使用 yt-dlp 下载媒体文件（视频或音频）
    支持 B站、YouTube、小宇宙播客等平台
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # 优先 mp4 格式，避免会员限制
    }

    # if list_formats:
    #     ydl_opts['listformats'] = True
    #     ydl_opts['simulate'] = True  # 模拟模式，只列出格式，不下载

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if list_formats:
                print(f"列出格式: {url}")
            else:
                print(f"开始下载: {url}")
            ydl.download([url])
            if not list_formats:
                print("下载完成！")
    except Exception as e:
        print(f"操作失败: {e}")

def main():
    parser = argparse.ArgumentParser(description="下载媒体文件")
    parser.add_argument('url', help='媒体URL')
    parser.add_argument('--list-formats', '-F', action='store_true', help='列出可用格式')

    args = parser.parse_args()

    download_media(args.url, list_formats=args.list_formats)

if __name__ == "__main__":
    main()
"""
```bash
# 下载 B站视频
python main.py https://www.bilibili.com/video/BV12CWrzqELo/?spm_id_from=333.1007.tianma.6-4-22.click

# 下载 YouTube 视频
python main.py https://www.youtube.com/watch?v=wjZofJX0v4M

# 下载小宇宙播客
python main.py https://www.xiaoyuzhoufm.com/episode/68f7034122654730207b940c
```

"""