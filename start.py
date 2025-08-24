import os
import sys
import subprocess
import signal
import threading
import time
from pathlib import Path

from config import get_config
from port_config import frontend_port, backend_port

ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"
BACKEND_ENTRY = ROOT / "main.py"



def start_frontend(port: int, backend_port: int) -> subprocess.Popen:
    # 使用 Vite 的 --port 参数
    cmd = [
        'npm', 'run', 'dev', '--', '--port', str(port)
    ]
    env = os.environ.copy()
    # 传递后端端口给 Vite（在 vite.config.ts 中通过 process.env.BACKEND_PORT 读取）
    env['BACKEND_PORT'] = str(backend_port)
    return subprocess.Popen(
        cmd,
        cwd=str(FRONTEND_DIR),
        shell=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
    )


def start_backend(port: int) -> subprocess.Popen:
    env = os.environ.copy()
    env['PORT'] = str(port)
    cmd = [sys.executable, str(BACKEND_ENTRY)]
    return subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        shell=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
    )




def stream_output(name: str, proc: subprocess.Popen):
    assert proc.stdout is not None
    for line in proc.stdout:
        print(f"[{name}] {line}", end='')


def main():
    # 启动后端和前端子进程，并在后台线程中流式打印它们的输出
    backend_proc = start_backend(backend_port)
    frontend_proc = start_frontend(frontend_port, backend_port)

    # 启动用于打印输出的线程
    t_back = threading.Thread(target=stream_output, args=("backend", backend_proc), daemon=True)
    t_front = threading.Thread(target=stream_output, args=("frontend", frontend_proc), daemon=True)
    t_back.start()
    t_front.start()

    try:
        # 等待直到任一子进程退出或用户中断
        while True:
            if backend_proc.poll() is not None or frontend_proc.poll() is not None:
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        # 收到中断信号，开始终止子进程
        print("收到中断，正在终止子进程...")
    finally:
        for p in (frontend_proc, backend_proc):
            if p and p.poll() is None:
                try:
                    p.terminate()
                except Exception:
                    pass
        # give processes a moment to exit
        time.sleep(0.5)
if __name__ == '__main__':
    main()
