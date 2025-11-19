"""最小化 Supabase 文件上传示例

基于 config.py 配置，使用 test.txt 文件进行测试。
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from supabase import create_client
from config import settings

def upload_file_example():
    """上传 test.txt 文件到 Supabase"""
    # 获取配置
    supabase_url = settings.supabase_url
    supabase_key = settings.supabase_key
    bucket = settings.supabase_bucket_name
    folder = settings.supabase_folder_name

    if not supabase_url or not supabase_key:
        print("Supabase 配置缺失")
        return

    # 创建客户端
    client = create_client(supabase_url, supabase_key)

    # 登录管理员账号（如果配置了）
    if settings.supabase_admin_email and settings.supabase_admin_password:
        try:
            client.auth.sign_in_with_password({
                "email": settings.supabase_admin_email,
                "password": settings.supabase_admin_password
            })
            print("Supabase 管理员登录成功")
        except Exception as e:
            print(f"Supabase 管理员登录失败: {e}")
            # 登录失败继续使用 anon key

    # 文件路径
    file_path = "test.txt"
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return

    # 读取文件
    with open(file_path, 'rb') as f:
        file_data = f.read()

    # 上传
    remote_path = f"{folder}/test.txt"
    try:
        response = client.storage.from_(bucket).upload(
            path=remote_path,
            file=file_data,
            file_options={"content-type": "text/plain"}
        )
        public_url = client.storage.from_(bucket).get_public_url(remote_path)
        print(f"上传成功，公开 URL: {public_url}")
    except Exception as e:
        print(f"上传失败: {e}")

if __name__ == "__main__":
    upload_file_example()
