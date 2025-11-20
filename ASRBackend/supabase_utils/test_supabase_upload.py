"""测试 Supabase 文件上传功能"""

from supabase_utils.supabase_upload import upload_file_to_supabase
import os

def test_upload():
    """测试上传文件"""
    # 使用 example_tests 目录下的 test.txt
    file_path = os.path.join(os.path.dirname(__file__), "example_tests", "test.txt")

    if not os.path.exists(file_path):
        print(f"测试文件不存在: {file_path}")
        return

    print(f"开始上传文件: {file_path}")
    success, result = upload_file_to_supabase(file_path)
    if success:
        print(f"上传成功: {result}")
    else:
        print(f"上传失败: {result}")

if __name__ == "__main__":
    test_upload()
