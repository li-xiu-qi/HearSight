# -*- coding: utf-8 -*-
"""测试文件上传和重命名功能"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:9999"


def test_unique_filename():
    """测试文件名唯一性逻辑"""
    from backend.routers.upload_router import get_unique_filename
    from pathlib import Path
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # 测试不存在的文件
        result = get_unique_filename(tmp_path, "test.mp4")
        assert result == "test.mp4", "不存在的文件应该返回原文件名"
        
        # 创建文件并测试冲突
        (tmp_path / "test.mp4").touch()
        result = get_unique_filename(tmp_path, "test.mp4")
        assert result == "test-1.mp4", "第一次冲突应该返回 test-1.mp4"
        
        # 创建更多冲突
        (tmp_path / "test-1.mp4").touch()
        result = get_unique_filename(tmp_path, "test.mp4")
        assert result == "test-2.mp4", "第二次冲突应该返回 test-2.mp4"
        
        (tmp_path / "test-2.mp4").touch()
        result = get_unique_filename(tmp_path, "test.mp4")
        assert result == "test-3.mp4", "第三次冲突应该返回 test-3.mp4"
        
        print("✓ 文件名唯一性测试通过")


def test_upload_api():
    """测试上传API"""
    test_file = Path(__file__).parent / "datas" / "test.mp3"
    
    if not test_file.exists():
        print(f"跳过上传测试: 测试文件不存在 {test_file}")
        return
    
    with open(test_file, "rb") as f:
        files = {"file": (test_file.name, f, "audio/mpeg")}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
    
    print(f"上传响应状态: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"上传成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data.get("data", {})
    else:
        print(f"上传失败: {response.text}")
        return None


def test_rename_api(old_filename: str):
    """测试重命名API"""
    payload = {
        "old_filename": old_filename,
        "new_filename": "renamed_test_audio.mp3"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/upload/rename",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"重命名响应状态: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"重命名成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data.get("data", {})
    else:
        print(f"重命名失败: {response.text}")
        return None


def test_rename_conflict():
    """测试文件名冲突自动处理"""
    print("测试文件名冲突处理:")
    
    # 假设已经有一个叫 test.mp4 的文件
    payloads = [
        {"old_filename": "file1.mp4", "new_filename": "test.mp4"},
        {"old_filename": "file2.mp4", "new_filename": "test.mp4"},
        {"old_filename": "file3.mp4", "new_filename": "test.mp4"},
    ]
    
    for i, payload in enumerate(payloads, 1):
        print(f"\n  尝试 {i}: 重命名为 test.mp4")
        response = requests.post(
            f"{BASE_URL}/api/upload/rename",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            new_name = data.get("data", {}).get("new_filename", "")
            print(f"  结果: {new_name}")
        else:
            print(f"  失败: {response.text}")


if __name__ == "__main__":
    print("开始测试文件上传和重命名功能\n")
    
    print("1. 测试文件名唯一性逻辑")
    test_unique_filename()
    print()
    
    print("2. 测试上传API")
    upload_result = test_upload_api()
    print()
    
    if upload_result and "basename" in upload_result:
        print("3. 测试重命名API")
        test_rename_api(upload_result["basename"])
        print()
    
    print("测试完成")
