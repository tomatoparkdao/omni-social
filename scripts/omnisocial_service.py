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


def owns(pid, kind, launcher_pid=None):
    candidate = process(pid)
    if candidate is None:
        return False
    try:
        command = ' '.join(candidate.cmdline())
        if kind == 'launcher':
            return Path(candidate.exe()).resolve() == PYTHON.resolve() and 'sau_backend.py' in command
        if kind == 'backend':
            return (candidate.pid == launcher_pid or candidate.ppid() == launcher_pid) and 'sau_backend.py' in command
        if kind == 'vite':
            return str(VITE) in command
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
    return False


def stop():
    if not STATE.is_file():
        print('No recorded OmniSocial processes; nothing stopped.')
        return
    saved = json.loads(STATE.read_text(encoding='utf-8'))
    launcher_pid = saved.get('backend_launcher')
    for key, kind in (('backend', 'backend'), ('backend_launcher', 'launcher'), ('frontend', 'vite')):
        pid = saved.get(key)
        if owns(pid, kind, launcher_pid):
            process(pid).terminate()
    STATE.unlink()
    print('Only recorded OmniSocial processes were stopped.')


def start():
    if not PYTHON.is_file():
        raise RuntimeError('Missing .venv Python; install the project environment first.')
    node = shutil.which('node')
    if not node:
        raise RuntimeError('Node.js is not on PATH.')
    if not VITE.is_file():
        npm = shutil.which('npm')
        if not npm:
            raise RuntimeError('npm is not on PATH.')
        subprocess.run([npm, 'install', '--no-audit', '--no-fund'], cwd=ROOT / 'sau_frontend', check=True)

    for port in (5409, 5173):
        owner = listener(port)
        if owner:
            candidate = process(owner)
            name = candidate.name() if candidate else 'unknown'
            raise RuntimeError(f'Port {port} is occupied by PID {owner} ({name}); no process was stopped.')

    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    backend = subprocess.Popen([str(PYTHON), 'sau_backend.py'], cwd=ROOT,
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, creationflags=flags)
    frontend = subprocess.Popen([node, str(VITE), '--host', '127.0.0.1'], cwd=ROOT / 'sau_frontend',
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, creationflags=flags)
    try:
        backend_pid = frontend_pid = None
        for _ in range(30):
            backend_pid, frontend_pid = listener(5409), listener(5173)
            if backend_pid and frontend_pid:
                break
            time.sleep(1)
        if not backend_pid or not frontend_pid or not owns(backend_pid, 'backend', backend.pid) or not owns(frontend_pid, 'vite'):
            raise RuntimeError('The services did not open their expected ports within 30 seconds.')
        with urllib.request.urlopen('http://127.0.0.1:5173/api/health', timeout=5) as response:
            if json.load(response).get('status') != 'ok':
                raise RuntimeError('Backend health check failed.')
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
