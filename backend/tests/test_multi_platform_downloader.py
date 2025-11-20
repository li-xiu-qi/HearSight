import sys
import os

# 添加项目根目录到路径，以便导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.media_processing import MediaDownloaderFactory

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

    factory = MediaDownloaderFactory(output_dir=test_out_dir)

    for url in test_urls:
        print(f"测试下载: {url}")
        try:
            result = factory.download(url)
            if result.success:
                file_path = result.video_path or result.audio_path
                print(f"下载成功，文件: {file_path}")
                # 检查文件是否存在
                if file_path and os.path.exists(file_path):
                    print(f"文件验证成功: {file_path}")
                else:
                    print(f"文件不存在: {file_path}")
            else:
                print(f"下载失败: {result.error_message}")
        except Exception as e:
            print(f"下载异常: {e}")
        print("-" * 50)

if __name__ == "__main__":
    test_multi_platform_downloader()