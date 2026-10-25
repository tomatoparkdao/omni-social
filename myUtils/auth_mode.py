"""Web 身份认证模式解析与校验。

两种模式：

- ``local_dev``  单机本地开发免登录，必须通过 ``OMNISOCIAL_AUTH_MODE=local_dev`` 显式开启。
- ``production`` 默认模式，服务端强制管理员密码登录。

``local_dev`` 必须同时满足以下全部条件，任一不满足即抛出 :class:`AuthModeError`：

1. 显式设置 ``OMNISOCIAL_AUTH_MODE=local_dev``（绝不根据访问 IP、Host 或 NODE_ENV 自动放行）；
2. ``OMNISOCIAL_ENV`` 不是 ``production``；
3. 声明的监听地址为回环地址，且进程实际监听的套接字全部为回环地址（不允许 ``0.0.0.0``）；
4. 未启用反向代理 / 隧道（``OMNISOCIAL_TRUST_PROXY`` 等开关不得为真）。

请求级追加校验由调用方（``sau_backend.protect_web_api``）完成：来源地址必须是回环、
Host 头必须是回环主机名、且不得携带任何代理头。
"""
from __future__ import annotations

import ipaddress
import os

LOCAL_DEV = 'local_dev'
PRODUCTION = 'production'
VALID_MODES = frozenset({LOCAL_DEV, PRODUCTION})

#: 出现这些请求头即视为经过代理 / 隧道，local_dev 免登录必须拒绝。
PROXY_HEADERS = (
    'X-Forwarded-For',
    'X-Forwarded-Host',
    'X-Forwarded-Proto',
    'X-Real-IP',
    'Forwarded',
    'CF-Connecting-IP',
    'True-Client-IP',
    'X-Original-Forwarded-For',
)

#: 出现这些环境变量开关且为真，说明部署在反向代理 / 公网隧道之后。
PROXY_ENV_FLAGS = ('OMNISOCIAL_TRUST_PROXY', 'OMNISOCIAL_BEHIND_PROXY', 'OMNISOCIAL_PUBLIC_TUNNEL')

_ENV_KEYS = ('OMNISOCIAL_AUTH_MODE', 'OMNISOCIAL_ENV', 'OMNISOCIAL_BIND_HOST') + PROXY_ENV_FLAGS
_cache = {}


class AuthModeError(RuntimeError):
    """认证模式配置不安全或含义不明确。"""


def _flag(name):
    return (os.environ.get(name) or '').strip().lower() in {'1', 'true', 'yes', 'on'}


def is_loopback(host):
    """判断主机名 / IP 字面量是否为回环地址。"""
    host = (host or '').strip().strip('[]').lower()
    if not host:
        return False
    if host == 'localhost':
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def is_loopback_host_header(value):
    """判断 Host 请求头（可含端口）是否指向回环地址。"""
    host = (value or '').strip()
    if not host:
        return False
    if host.startswith('['):
        end = host.find(']')
        return is_loopback(host[1:end]) if end > 0 else False
    if host.count(':') == 1:
        host = host.rsplit(':', 1)[0]
    return is_loopback(host)


def _listening_addresses():
    """返回本进程正在监听的地址集合；无法获取时返回 None。"""
    try:
        import psutil
    except ImportError:  # pragma: no cover - psutil 为运行依赖
        return None
    try:
        connections = psutil.net_connections(kind='inet')
    except (psutil.AccessDenied, OSError):  # pragma: no cover - 平台差异
        return None
    addresses = set()
    pid = os.getpid()
    for connection in connections:
        if connection.pid != pid or connection.status != psutil.CONN_LISTEN or not connection.laddr:
            continue
        ip = getattr(connection.laddr, 'ip', None) or connection.laddr[0]
        addresses.add(ip)
    return addresses


def _compute():
    raw = (os.environ.get('OMNISOCIAL_AUTH_MODE') or '').strip().lower()
    if not raw:
        # 未显式配置一律按生产模式处理：默认不提供任何免登录通道。
        return PRODUCTION
    if raw not in VALID_MODES:
        raise AuthModeError(
            f'OMNISOCIAL_AUTH_MODE 取值无效：{raw!r}，只允许 local_dev 或 production'
        )
    if raw == PRODUCTION:
        return PRODUCTION

    if (os.environ.get('OMNISOCIAL_ENV') or '').strip().lower() == 'production':
        raise AuthModeError('OMNISOCIAL_ENV=production 时禁止启用 local_dev 免登录')

    for flag in PROXY_ENV_FLAGS:
        if _flag(flag):
            raise AuthModeError(f'local_dev 免登录不能与反向代理 / 隧道同时启用（{flag}）')

    bind_host = (os.environ.get('OMNISOCIAL_BIND_HOST') or '127.0.0.1').strip()
    if not is_loopback(bind_host):
        raise AuthModeError(
            f'local_dev 免登录要求只监听回环地址，当前 OMNISOCIAL_BIND_HOST={bind_host}'
        )

    addresses = _listening_addresses()
    external = sorted(address for address in (addresses or ()) if not is_loopback(address))
    if external:
        raise AuthModeError(
            'local_dev 免登录检测到非回环监听地址：' + ', '.join(external)
        )
    return LOCAL_DEV


def resolve_auth_mode():
    """返回当前生效的认证模式；配置不安全时抛出 :class:`AuthModeError`。"""
    signature = tuple(os.environ.get(key, '') for key in _ENV_KEYS)
    if signature not in _cache:
        _cache[signature] = _compute()
    return _cache[signature]


def clear_cache():
    """清空解析缓存（测试与配置热更新使用）。"""
    _cache.clear()
