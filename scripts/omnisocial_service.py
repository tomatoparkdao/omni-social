"""Start/stop only this project's recorded Windows processes."""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import psutil


ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / '.venv' / 'Scripts' / 'python.exe'
VITE = ROOT / 'sau_frontend' / 'node_modules' / 'vite' / 'bin' / 'vite.js'
STATE = ROOT / '.local' / 'omnisocial-pids.json'


def listener(port):
    for connection in psutil.net_connections(kind='inet'):
        if connection.status == psutil.CONN_LISTEN and connection.laddr.port == port:
            return connection.pid
    return None


def process(pid):
    try:
        return psutil.Process(int(pid)) if pid else None
    except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
        return None


def owns(pid, kind=None, launcher_pid=None):
    """核验进程是否属于本项目：命令行 + 工作目录双重校验。"""
    candidate = process(pid)
    if candidate is None:
        return False
    try:
        command = ' '.join(candidate.cmdline())
        cwd = os.path.normcase(str(Path(candidate.cwd()).resolve()))
        if 'sau_backend.py' in command:
            return cwd == os.path.normcase(str(ROOT))
        if 'vite' in command and 'node_modules' in command:
            return cwd == os.path.normcase(str(ROOT / 'sau_frontend'))
    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
        return False
    return False


def stop():
    stopped = []
    if STATE.is_file():
        saved = json.loads(STATE.read_text(encoding='utf-8'))
        for key in ('backend', 'backend_launcher', 'frontend'):
            pid = saved.get(key)
            if owns(pid):
                process(pid).terminate()
                stopped.append(pid)
    # 记录丢失或子进程未记录时，按端口找回本项目自己的进程，避免下次启动被自己挡住。
    for port in (5409, 5173):
        owner = listener(port)
        if owner and owner not in stopped and owns(owner):
            process(owner).terminate()
            stopped.append(owner)
    if STATE.is_file():
        STATE.unlink()
    print(f'Stopped {len(stopped)} OmniSocial process(es): {sorted(set(stopped))}' if stopped
          else 'No OmniSocial processes were running; nothing stopped.')


def log_tail(path, limit=8):
    """读取日志末尾若干行，用于启动失败时给出清晰原因。"""
    try:
        lines = path.read_text(encoding='utf-8', errors='replace').strip().splitlines()
    except OSError:
        return 'no backend log available'
    return ' | '.join(lines[-limit:]) if lines else 'backend log is empty'


def child_env():
    """为本机启动的子进程准备环境变量，并校验认证模式配置。"""
    env = os.environ.copy()
    auth_mode = (env.get('OMNISOCIAL_AUTH_MODE') or '').strip().lower()
    if auth_mode not in {'local_dev', 'production'}:
        raise RuntimeError(
            'OMNISOCIAL_AUTH_MODE 未设置：本机启动请设置 local_dev，正式部署请设置 production。')
    if auth_mode == 'local_dev':
        if (env.get('OMNISOCIAL_ENV') or '').strip().lower() == 'production':
            raise RuntimeError('OMNISOCIAL_ENV=production 时禁止启用 local_dev 免登录。')
        env['OMNISOCIAL_BIND_HOST'] = '127.0.0.1'
        env.setdefault('OMNISOCIAL_ENV', 'local')
    elif not env.get('OMNISOCIAL_SESSION_SECRET') or not env.get('OMNISOCIAL_ADMIN_PASSWORD_HASH'):
        raise RuntimeError('production 认证模式需要 OMNISOCIAL_SESSION_SECRET 与 OMNISOCIAL_ADMIN_PASSWORD_HASH。')
    return env


def live_state(env):
    """若本项目前后端已在运行且认证模式符合预期，返回会话状态，否则返回 None。"""
    owners = [listener(5409), listener(5173)]
    if not all(owner and owns(owner) for owner in owners):
        return None
    try:
        with urllib.request.urlopen('http://127.0.0.1:5173/api/auth/session', timeout=5) as response:
            state = json.load(response)
    except OSError:
        return None
    expected_mode = (env.get('OMNISOCIAL_AUTH_MODE') or '').strip().lower()
    return state if state.get('mode') == expected_mode else None


def start():
    if not PYTHON.is_file():
        raise RuntimeError('Missing .venv Python; install the project environment first.')
    env = child_env()
    node = shutil.which('node')
    if not node:
        raise RuntimeError('Node.js is not on PATH.')
    if not VITE.is_file():
        npm = shutil.which('npm')
        if not npm:
            raise RuntimeError('npm is not on PATH.')
        subprocess.run([npm, 'install', '--no-audit', '--no-fund'], cwd=ROOT / 'sau_frontend', check=True)

    state = live_state(env)
    if state is not None:
        print(f"OmniSocial is already running at http://127.0.0.1:5173 (auth mode {state.get('mode')})")
        if sys.platform == 'win32':
            os.startfile('http://127.0.0.1:5173')
        return

    for port in (5409, 5173):
        owner = listener(port)
        if owner:
            candidate = process(owner)
            name = candidate.name() if candidate else 'unknown'
            raise RuntimeError(f'Port {port} is occupied by PID {owner} ({name}); no process was stopped.')

    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    env.setdefault('PYTHONUNBUFFERED', '1')
    log_dir = ROOT / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    backend_log = open(log_dir / 'backend-dev.log', 'a', encoding='utf-8')
    try:
        backend = subprocess.Popen([str(PYTHON), 'sau_backend.py'], cwd=ROOT, env=env,
                                   stdin=subprocess.DEVNULL, stdout=backend_log,
                                   stderr=subprocess.STDOUT, creationflags=flags)
        frontend = subprocess.Popen([node, str(VITE), '--host', '127.0.0.1'], cwd=ROOT / 'sau_frontend', env=env,
                                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, creationflags=flags)
    finally:
        backend_log.close()
    backend_pid = frontend_pid = None
    try:
        for _ in range(30):
            if backend.poll() is not None:
                raise RuntimeError(f'Backend exited during startup: {log_tail(log_dir / "backend-dev.log")}')
            backend_pid, frontend_pid = listener(5409), listener(5173)
            if backend_pid and frontend_pid:
                break
            time.sleep(1)
        if not backend_pid or not frontend_pid or not owns(backend_pid, 'backend', backend.pid) or not owns(frontend_pid, 'vite'):
            raise RuntimeError(f'Services did not open their expected ports within 30 seconds: {log_tail(log_dir / "backend-dev.log")}')
        with urllib.request.urlopen('http://127.0.0.1:5173/api/health', timeout=5) as response:
            if json.load(response).get('status') != 'ok':
                raise RuntimeError('Backend health check failed.')
        with urllib.request.urlopen('http://127.0.0.1:5173/api/auth/session', timeout=5) as response:
            session_state = json.load(response)
        expected_mode = (env.get('OMNISOCIAL_AUTH_MODE') or '').strip().lower()
        if session_state.get('mode') != expected_mode:
            raise RuntimeError(
                f'认证模式不匹配：期望 {expected_mode}，实际 {session_state.get("mode")}。'
                '请确认没有其他 OmniSocial 实例占用 5409 端口。')
        if expected_mode == 'local_dev' and session_state.get('authenticated') is not True:
            raise RuntimeError('本机开发模式未能启用免登录，请查看 logs\\backend-dev.log。')
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps({'backend_launcher': backend.pid, 'backend': backend_pid,
                                     'frontend': frontend_pid}), encoding='utf-8')
    except Exception:
        for child in (process(backend_pid), process(frontend.pid)):
            if child and child.is_running():
                child.terminate()
        if backend.poll() is None:
            backend.terminate()
        raise
    print('OmniSocial is running at http://127.0.0.1:5173')
    if sys.platform == 'win32':
        os.startfile('http://127.0.0.1:5173')


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in {'start', 'stop'}:
        raise SystemExit('Usage: omnisocial_service.py start|stop')
    try:
        (start if sys.argv[1] == 'start' else stop)()
    except Exception as exc:
        print(f'OmniSocial service operation failed: {exc}', file=sys.stderr)
        raise SystemExit(1)
