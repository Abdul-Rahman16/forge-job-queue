import time
import signal
import sys

from core.db import SessionLocal
from core.logging import configure_logging, log
from domain.queue import claim_task, complete_task, fail_task

configure_logging()

running = True


def handle_shutdown(signum, frame):
    global running
    log.info("shutdown_signal_received")
    running = False


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


def process_task(task) -> bool:
    log.info("task_processing", task_id=str(task.id), payload=task.payload)
    time.sleep(1)
    return True


def run_worker():
    log.info("worker_started")
    while running:
        db = SessionLocal()
        try:
            task = claim_task(db)
            if task is None:
                db.close()
                time.sleep(2)
                continue

            success = process_task(task)
            if success:
                complete_task(db, task)
                log.info("task_completed", task_id=str(task.id))
            else:
                fail_task(db, task)
                log.warning("task_failed_retrying", task_id=str(task.id))
        finally:
            db.close()

    log.info("worker_stopped")
    sys.exit(0)


if __name__ == "__main__":
    run_worker()