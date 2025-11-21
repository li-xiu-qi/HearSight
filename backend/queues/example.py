# -*- coding: utf-8 -*-
"""实际任务执行和进度监控示例"""

import time
import sys
import argparse
from pathlib import Path

# 将项目根目录加入 sys.path，确保 import backend 包正确（支持在 queues 目录直接运行该脚本）
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.queues.tasks import process_job_task
from backend.routers.progress_router import get_task_progress, set_task_progress, redis_client
from backend.config import create_celery_app, settings


def demo_real_task_execution():
    """演示实际任务执行和进度监控"""
    print("=== 实际任务执行演示 ===")

    # 使用实际的B站视频链接进行测试
    test_url = "https://www.bilibili.com/video/BV1uL15BBEB4/?spm_id_from=333.1007.tianma.1-1-1.click"
    job_id = 99999  # 测试用的job_id

    # 设置必要的参数
    static_dir = str(Path(settings.downloads_dir).resolve())
    db_url = None  # 测试时可以不使用数据库

    print(f"测试URL: {test_url}")
    print(f"任务ID: {job_id}")
    print(f"静态目录: {static_dir}")

    try:
        # 仅保留 async 模式: 通过 Celery worker 执行任务

        # 异步模式：提交到 Celery 队列（需要有 worker 正在运行）
        print("\n--- 提交Celery任务（异步） ---")
        task = process_job_task.delay(
            job_id=job_id,
            url=test_url,
            static_dir=static_dir,
            db_url=db_url,
        )

        print(f"任务已提交!")
        print(f"Celery Task ID: {task.id}")
        print(f"任务状态: {task.status}")
        # 打印 Redis 连接与 key 初始值，方便调试
        try:
            print(f"Celery broker URL: {settings.celery_broker_url}")
            print(f"Celery result backend: {settings.celery_result_backend}")
            key = f"task_progress:{job_id}"
            raw = redis_client.get(key)
            print(f"初始 Redis key({key}) value: {raw}")
        except Exception as e:
            print(f"无法读取Redis: {e}")

        # 创建Celery app 实例，用于查询任务状态
        celery_app = create_celery_app()

        # 在提交之前初始化进度（模拟API行为）
        try:
            set_task_progress(job_id, {
                "status": "pending",
                "stage": "download_start",
                "progress_percent": 0,
                "filename": "",
                "message": "任务已创建，等待处理",
                "job_id": job_id,
            })
        except Exception as e:
            print(f"初始化进度失败: {e}")

        # 立即做一个直接的 Redis 写入/读取测试，确认进度Redis可用且是同一个DB
        try:
            test_key = f"test_progress_connection:{job_id}"
            redis_client.setex(test_key, 60, "ok")
            test_value = redis_client.get(test_key)
            print(f"Redis test write/read key={test_key}, value={test_value}")
        except Exception as e:
            print(f"Redis 写入/读取测试失败: {e}")

        # 监控任务进度
        print("\n--- 监控任务进度 ---")
        max_wait_time = 600  # 最多等待10分钟
        wait_count = 0

        while wait_count < max_wait_time:
            try:
                # 获取当前进度
                progress = get_task_progress(job_id)

                print(f"[{wait_count}s] 状态: {progress.get('status', 'unknown')} | "
                      f"阶段: {progress.get('stage', 'unknown')} | "
                      f"进度: {progress.get('progress_percent', 0)}% | "
                      f"消息: {progress.get('message', '')}")

                # 检查任务是否完成
                if progress.get('status') in ['completed', 'success', 'failed']:
                    print(f"\n任务完成! 最终状态: {progress.get('status')}")
                    if progress.get('status') == 'failed':
                        print(f"错误信息: {progress.get('error', '未知错误')}")
                    break

                # 检查Celery任务状态（通过重新创建 AsyncResult 获取最新状态）
                current_task = celery_app.AsyncResult(task.id)
                if current_task.status == 'SUCCESS':
                    print(f"\nCelery任务成功完成!")
                    print(f"任务结果: {current_task.result}")
                    break
                elif current_task.status == 'FAILURE':
                    print(f"\nCelery任务失败!")
                    print(f"错误信息: {current_task.info}")
                    break

            except Exception as e:
                print(f"获取进度时出错: {e}")
            finally:
                # 每次轮询时，打印Redis当前值，便于追踪是否被worker写入
                try:
                    raw = redis_client.get(key)
                    print(f"Redis raw: {raw}")
                except Exception:
                    pass

            time.sleep(5)  # 每5秒检查一次
            wait_count += 5

        if wait_count >= max_wait_time:
            print("\n等待超时，任务可能仍在后台执行")

        print("\n=== 演示结束 ===")

        # 结束后列出匹配键，确认是否存有task_progress
        try:
            keys = redis_client.keys('task_progress:*')
            print(f"All task_progress keys: {keys}")
        except Exception as e:
            print(f"列出task_progress keys失败: {e}")

    except Exception as e:
        print(f"提交任务时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='示例：提交任务到 Celery 并监控进度（需要 worker 运行）')
    args = parser.parse_args()
    demo_real_task_execution()
