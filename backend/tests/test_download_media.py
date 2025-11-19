import os
import pytest
from download_media_file import download_media

@pytest.mark.parametrize("platform, url", [
    ("youtube", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    ("bilibili", "https://www.bilibili.com/video/BV1yFs3zJEhd"),
    ("xiaoyuzhou", "https://www.xiaoyuzhoufm.com/episode/68f7034122654730207b940c"),
])
def test_multi_platform_download(platform, url):
    """Test download functionality for multiple platforms"""
    test_dir = f"test_downloads_{platform}"
    try:
        # Execute download
        download_media(url, output_dir=test_dir)
        
        # Verify files were created
        assert os.path.exists(test_dir), f"Download directory not created for {platform}"
        files = os.listdir(test_dir)
        assert len(files) > 0, f"No files downloaded for {platform}"
        assert any(f.endswith(('.mp4', '.mp3', '.m4a')) for f in files), f"No media files found for {platform}"
    finally:
        # Cleanup
        if os.path.exists(test_dir):
            for file in os.listdir(test_dir):
                os.remove(os.path.join(test_dir, file))
            os.rmdir(test_dir)


def test_url_validation():
    """Test URL validation logic"""
    invalid_urls = [
        "example.com/video",  # Missing protocol
        "https://unsupportedplatform.com/video",  # Unsupported platform
        "",  # Empty URL
    ]
    
    test_dir = "test_invalid_urls"
    for url in invalid_urls:
        try:
            download_media(url, output_dir=test_dir)
            # If no exception is raised, the test fails
            assert False, f"Expected error for invalid URL: {url}"
        except Exception as e:
            # Verify it's a meaningful error
            assert str(e), f"No error message for invalid URL: {url}"
        finally:
            if os.path.exists(test_dir):
                for file in os.listdir(test_dir):
                    os.remove(os.path.join(test_dir, file))
                os.rmdir(test_dir)
