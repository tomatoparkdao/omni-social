"""Persistent Web task worker, disabled until real publication is explicitly enabled.

An interrupted in-flight task becomes needs_review, never automatically retried.
"""
import argparse
import asyncio
import logging
import time

from conf import BASE_DIR
from myUtils import task_store, web_task_adapter
from myUtils.publish_guard import require_real_publish_enabled


logger = logging.getLogger(__name__)


async def run_once(base_dir, executor=None):
    require_real_publish_enabled()
    task = task_store.claim_due_task(base_dir)
    if task is None:
        return False
    try:
        web_task_adapter.prepare_task(base_dir, task)
    except ValueError as exc:
        task_store.finish_task(base_dir, task['id'], 'failed', str(exc))
        return True
    try:
        await (executor or web_task_adapter.execute_task)(base_dir, task)
    except Exception as exc:
        logger.error('任务 %s 执行结果不确定：%s', task['id'], exc.__class__.__name__)
        task_store.finish_task(base_dir, task['id'], 'needs_review', 'execution_unknown')
    else:
        task_store.finish_task(base_dir, task['id'], 'submitted_unverified')
    return True


def main():
    parser = argparse.ArgumentParser(description='OmniSocial Web publication worker')
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    require_real_publish_enabled()
    task_store.recover_running_tasks(BASE_DIR)
    while True:
        processed = asyncio.run(run_once(BASE_DIR))
        if args.once:
            break
        if not processed:
            time.sleep(1)


if __name__ == '__main__':
    main()
