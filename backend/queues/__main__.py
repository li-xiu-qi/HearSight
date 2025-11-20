# -*- coding: utf-8 -*-
"""Celery worker模块入口"""

from backend.queues.worker_launcher import main

if __name__ == "__main__":
    main()
