import sys
import os

# 添加项目根目录到路径，以便导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.utils.vedio_utils.download_video.multi_platform_downloader import MultiPlatformDownloader

def test_multi_platform_downloader():
    """测试多平台下载器"""
    # 测试URL列表
    test_urls = [
        "https://www.bilibili.com/video/BV12CWrzqELo/?spm_id_from=333.1007.tianma.6-4-22.click",  # B站视频
        "https://www.youtube.com/watch?v=wjZofJX0v4M",  # YouTube视频
        "https://www.xiaoyuzhoufm.com/episode/68f7034122654730207b940c"  # 小宇宙播客
    ]

    # 创建测试下载目录
    test_out_dir = os.path.join(os.path.dirname(__file__), 'test_downloads')
    if not os.path.exists(test_out_dir):
        os.makedirs(test_out_dir)

    for url in test_urls:
        print(f"测试下载: {url}")
        try:
            downloader = MultiPlatformDownloader(url, out_dir=test_out_dir)
            files = downloader.download()
            print(f"下载成功，文件: {files}")
            # 检查目录中的文件
            if os.path.exists(test_out_dir):
                existing_files = os.listdir(test_out_dir)
                print(f"目录中的文件: {existing_files}")
        except Exception as e:
            print(f"下载失败: {e}")
        print("-" * 50)

if __name__ == "__main__":
    test_multi_platform_downloader()