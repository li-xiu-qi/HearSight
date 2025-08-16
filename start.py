import os
import sys
import subprocess
import signal
from pathlib import Path

# 尝试使用 PyYAML；若不可用则使用简易 YAML 解析（针对当前简单结构足够）
try:
    import yaml  # type: ignore
except Exception:  # 遵守用户规则：尽量少 try/except，仅用于可选依赖降级
    yaml = None  # type: ignore

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.yaml"
FRONTEND_DIR = ROOT / "frontend"
BACKEND_ENTRY = ROOT / "main.py"


def _simple_yaml_load(text: str) -> dict:
    """
    极简 YAML 解析，仅支持两层字典：
    bilibili:
      from_env: true
      sessdata: ""
    server:
      frontend_port: 5173
      backend_port: 8000
    """
    result: dict = {}
    stack = [result]
    last_indent = 0
    path_stack = []
    for line in text.splitlines():
        s = line.rstrip()
        if not s or s.lstrip().startswith('#'):
            continue
        indent = len(s) - len(s.lstrip(' '))
        s = s.strip()
        if ':' in s:
            key, val = s.split(':', 1)
            key = key.strip()
            val = val.strip()
            # 层级调整
            while path_stack and indent <= last_indent:
                stack.pop()
                path_stack.pop()
                last_indent -= 2
            if val == '':
                # 新字典节点
                d = {}
                stack[-1][key] = d
                stack.append(d)
                path_stack.append(key)
                last_indent = indent
            else:
                # 解析标量
                if val.lower() in ('true', 'false'):
                    v = val.lower() == 'true'
                elif val.startswith('"') and val.endswith('"'):
                    v = val[1:-1]
                elif val.isdigit():
                    v = int(val)
                else:
                    v = val
                stack[-1][key] = v
                last_indent = indent
    return result


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {
            'server': {
                'frontend_port': 5173,
                'backend_port': 8000,
            }
        }
    txt = CONFIG_PATH.read_text(encoding='utf-8')
    if yaml is not None:
        data = yaml.safe_load(txt) or {}
    else:
        data = _simple_yaml_load(txt)
    return data or {}


def start_frontend(port: int) -> subprocess.Popen:
    # 使用 Vite 的 --port 参数
    cmd = [
        'npm', 'run', 'dev', '--', '--port', str(port)
    ]
    return subprocess.Popen(
        cmd,
        cwd=str(FRONTEND_DIR),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
    )


def start_backend(port: int) -> subprocess.Popen:
    env = os.environ.copy()
    env['PORT'] = str(port)
    # 若 main.py 不存在或为空，也允许运行（可能立即退出）
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
    )


def stream_output(name: str, proc: subprocess.Popen):
    assert proc.stdout is not None
    for line in proc.stdout:
        print(f"[{name}] {line}", end='')


def main():
    cfg = load_config()
    server_cfg = (cfg.get('server') or {})
    fe_port = int(server_cfg.get('frontend_port', 5173))
    be_port = int(server_cfg.get('backend_port', 8000))

    print(f"Starting frontend on http://localhost:{fe_port}")
    fe_proc = start_frontend(fe_port)

    print(f"Starting backend on http://localhost:{be_port}")
    be_proc = start_backend(be_port)

    procs = {
        'frontend': fe_proc,
        'backend': be_proc,
    }

    def shutdown(*_args):
        print("\nShutting down...")
        for p in procs.values():
            try:
                if p.poll() is None:
                    p.terminate()
            except Exception:
                pass
        # 等待结束
        for p in procs.values():
            try:
                p.wait(timeout=5)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, 'SIGTERM'):
        try:
            signal.signal(signal.SIGTERM, shutdown)
        except Exception:
            pass

    # 交替读取输出
    try:
        while True:
            alive = False
            for name, p in list(procs.items()):
                if p.poll() is None:
                    alive = True
                    if p.stdout and not p.stdout.closed:
                        line = p.stdout.readline()
                        if line:
                            print(f"[{name}] {line}", end='')
                else:
                    code = p.returncode
                    print(f"[{name}] exited with code {code}")
                    # 保持脚本运行，但不再读取该进程
                    procs.pop(name, None)
            if not procs:
                break
    except KeyboardInterrupt:
        shutdown()


if __name__ == '__main__':
    main()
