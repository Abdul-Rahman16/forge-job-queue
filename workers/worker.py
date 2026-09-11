import time
import signal
import sys

from core.db import SessionLocal
from domain.queue import claim_task, complete_task, fail_task

running = True


def handle_shutdown(signum, frame):
    global running
    print("Shutdown signal received, finishing current task then exiting...")
    running = False


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


def process_task(task) -> bool:
    """
    Placeholder job logic. Replace this with real work later.
    Return True on success, False to trigger a retry.
    """
    print(f"Processing task {task.id} with payload {task.payload}")
    time.sleep(1)  # pretend to do work
    return True


def run_worker():
    print("Worker started. Polling for tasks...")
    while running:
        db = SessionLocal()
        try:
            task = claim_task(db)
            if task is None:
                db.close()
                time.sleep(2)  # nothing to do, wait before polling again
                continue

            success = process_task(task)
            if success:
                complete_task(db, task)
                print(f"Task {task.id} completed.")
            else:
                fail_task(db, task)
                print(f"Task {task.id} failed, will retry with backoff.")
        finally:
            db.close()

    print("Worker stopped cleanly.")
    sys.exit(0)


if __name__ == "__main__":
    run_worker()