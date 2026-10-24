"""Default-off gate shared by real publication entry points."""
import os


def require_real_publish_enabled() -> None:
    if os.environ.get("OMNISOCIAL_ENABLE_REAL_PUBLISH") != "1":
        raise PermissionError("真实发布已关闭；当前只能创建和验证模拟任务")
