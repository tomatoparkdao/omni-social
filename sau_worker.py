"""Isolated mock queue worker. It never imports a real uploader."""
import argparse
import os
import time

from conf import BASE_DIR
from myUtils import task_store


def run_once(base_dir, adapter):
    task = task_store.claim_mock_task(base_dir)
    if task is None:
        return False
    try:
        adapter(task)
    except Exception:
        task_store.finish_mock_task(base_dir, task['id'], False, 'mock_adapter_failed')
    else:
        task_store.finish_mock_task(base_dir, task['id'], True)
    return True


def main():
    parser = argparse.ArgumentParser(description='OmniSocial isolated mock task worker')
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    if os.environ.get('OMNISOCIAL_ENV') != 'test':
        raise SystemExit('模拟 Worker 只能在 OMNISOCIAL_ENV=test 下运行')
    task_store.recover_mock_tasks(BASE_DIR)
    while True:
        processed = run_once(BASE_DIR, lambda task: None)
        if args.once:
            break
        if not processed:
            time.sleep(1)


if __name__ == '__main__':
    main()
