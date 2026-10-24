"""Create a consistent local SQLite backup without touching account cookies."""
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from conf import BASE_DIR


def backup_database(base_dir=BASE_DIR):
    source = Path(base_dir) / 'db' / 'database.db'
    if not source.is_file():
        raise FileNotFoundError('数据库不存在')
    target_dir = Path(base_dir) / 'db' / 'backups'
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"omnisocial-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.db"
    with closing(sqlite3.connect(f'file:{source}?mode=ro', uri=True)) as src:
        with closing(sqlite3.connect(target)) as dst:
            src.backup(dst)
    os.chmod(target, 0o600)
    return target


if __name__ == '__main__':
    print(backup_database())
