"""Supabase 文件上传工具模块

提供文件上传到 Supabase 存储的功能，支持管理员登录。
"""

import sys
import os
import json
import uuid
from datetime import datetime
from typing import Optional, Tuple

# 添加 backend 路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import settings

from supabase import create_client, Client

from config import settings

# 全局客户端，避免重复登录
_supabase_client: Optional[Client] = None

# 文件名映射存储路径 - 使用config中的配置
# FILENAME_MAPPING_FILE = settings.filename_mapping_file  # 转录场景不需要映射文件


from supabase import create_client, Client
from config import settings

# 全局客户端，避免重复登录
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """获取或创建Supabase客户端（带缓存，避免重复登录）"""
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    # 获取配置
    supabase_url = settings.supabase_url
    supabase_key = settings.supabase_key

    if not supabase_url or not supabase_key:
        print("Supabase 配置缺失")
        return None

    # 创建客户端
    _supabase_client = create_client(supabase_url, supabase_key)

    # 登录管理员账号（如果配置了）
    if settings.supabase_admin_email and settings.supabase_admin_password:
        try:
            _supabase_client.auth.sign_in_with_password({
                "email": settings.supabase_admin_email,
                "password": settings.supabase_admin_password
            })
            print("Supabase 管理员登录成功")
        except Exception as e:
            print(f"Supabase 管理员登录失败: {e}")
            # 登录失败继续使用 anon key

    return _supabase_client


def upload_file_to_supabase(file_path: str, remote_path: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    """上传文件到 Supabase 存储

    Args:
        file_path: 本地文件路径
        remote_path: 远程路径（可选，默认使用UUID + 扩展名）

    Returns:
        (success: bool, result: str, uuid_name: str) - 成功时result为URL，uuid_name为生成的UUID文件名，失败时result为错误信息
    """
    # 获取客户端
    client = get_supabase_client()
    if client is None:
        return False, "Supabase配置缺失", None

    # 获取配置
    bucket = settings.supabase_bucket_name
    folder = settings.supabase_folder_name

    # 检查文件是否存在
    if not os.path.exists(file_path):
        return False, f"文件不存在: {file_path}", None

    # 获取原始文件名
    original_file_name = os.path.basename(file_path)
    file_ext = os.path.splitext(original_file_name)[1]

    # 生成UUID文件名
    uuid_name = f"{uuid.uuid4().hex}{file_ext}"

    # 确定远程路径
    if remote_path is None:
        remote_path = f"{folder}/{uuid_name}"

    # 读取文件
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
    except Exception as e:
        return False, f"读取文件失败: {e}", None

    # 上传
    try:
        response = client.storage.from_(bucket).upload(
            path=remote_path,
            file=file_data,
            file_options={"content-type": "application/octet-stream", "upsert": "true"}
        )
        public_url = client.storage.from_(bucket).get_public_url(remote_path)

        # 记录文件名映射
        # add_filename_mapping(original_file_name, uuid_name, remote_path)  # 转录场景不需要映射

        print(f"上传成功，公开 URL: {public_url}")
        print(f"原始文件名: {original_file_name} -> UUID文件名: {uuid_name}")

        return True, public_url, uuid_name
    except Exception as e:
        error_msg = str(e)
        print(f"上传失败: {error_msg}")
        return False, error_msg, None


def delete_file_from_supabase(uuid_name: str) -> bool:
    """从 Supabase 删除文件

    Args:
        uuid_name: UUID 文件名（不含扩展名）

    Returns:
        bool: 删除是否成功
    """
    try:
        # 获取客户端
        client = get_supabase_client()
        if not client:
            print("Supabase 客户端初始化失败")
            return False

        bucket = settings.supabase_bucket_name
        folder = settings.supabase_folder_name

        # 构建远程路径
        remote_path = f"{folder}/asr/{uuid_name}.wav"

        # 删除文件
        response = client.storage.from_(bucket).remove([remote_path])

        if response:
            print(f"Supabase 文件删除成功: {remote_path}")

            # 从映射表中移除记录（转录场景不需要）
            # remove_filename_mapping(uuid_name)

            return True
        else:
            print(f"Supabase 文件删除失败: {remote_path}")
            return False

    except Exception as e:
        error_msg = str(e)
        print(f"删除 Supabase 文件失败: {error_msg}")
        return False