# -*- coding: utf-8 -*-
"""测试bilibili cookie处理"""

import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
project_root = os.path.dirname(backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.media_processing.video.download.bilibili.bilibili_login_handler import (
    login_and_get_cookies_sync,
    load_cookies,
    save_cookies,
)

def test_login_and_get_cookies():
    """测试登录并获取cookie"""
    print("开始测试登录和获取cookie...")
    cookies = login_and_get_cookies_sync(headless=False)

    if cookies:
        print(f"✓ 成功获取cookie，共{len(cookies)}个")
        print("Cookie内容:")
        for c in cookies:
            name = c.get('name')
            value = c.get('value')
            print(f"  {name}: {value[:50]}..." if len(str(value)) > 50 else f"  {name}: {value}")
        return True
    else:
        print("✗ 获取cookie失败")
        return False

def test_load_cookies():
    """测试加载保存的cookie"""
    print("\n开始测试加载保存的cookie...")
    cookies = load_cookies()

    if cookies:
        print(f"✓ 成功加载cookie，共{len(cookies)}个")
        print("Cookie内容:")
        for c in cookies:
            name = c.get('name')
            value = c.get('value')
            print(f"  {name}: {value[:50]}..." if len(str(value)) > 50 else f"  {name}: {value}")
        return True
    else:
        print("✗ 未找到保存的cookie")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Bilibili Cookie处理测试")
    print("=" * 60)

    if test_load_cookies():
        print("\n已有保存的cookie，无需重新登录")
    else:
        test_login_and_get_cookies()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
