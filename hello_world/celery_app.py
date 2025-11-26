import os
import time
import json
from typing import Any, Dict
from celery import Celery
from celery.utils.log import get_task_logger

try:
    import redis as redispy
except Exception:
    redispy = None

logger = get_task_logger(__name__)

BROKER = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

celery = Celery("celery_app", broker=BROKER, backend=BACKEND)


@celery.task(name="celery_app.add")
def add(a: Any, b: Any) -> int:
    """Return integer sum of a and b. Logs and re-raises on error."""
    try:
        return int(a) + int(b)
    except Exception:
        logger.exception("add() failed with a=%r b=%r", a, b)
        raise


@celery.task(bind=True, name="celery_app.long_task")
def long_task(self, total: int = 5, delay: float = 1.0) -> Dict[str, Any]:
    """Publish progress updates to Redis pub/sub channel for this task.

    Messages are published as JSON strings to `task-progress:<task_id>`.
    """
    chan = f"task-progress:{self.request.id}"
    if redispy is None:
        for _ in range(int(total)):
            time.sleep(float(delay))
        return {"status": "no-redis", "task_id": self.request.id}

    r = redispy.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0)
    try:
        for i in range(1, int(total) + 1):
            time.sleep(float(delay))
            progress = int(i * 100 / int(total))
            msg = json.dumps({"task_id": self.request.id, "progress": progress})
            r.publish(chan, msg)
        r.publish(chan, "DONE")
    except Exception:
        logger.exception("Failed to publish progress for %s", self.request.id)
    return {"status": "completed", "task_id": self.request.id}


# simple beat schedule for quick verification (every 30s)
celery.conf.beat_schedule = {
    'periodic-add': {
        'task': 'celery_app.add',
        'schedule': 30.0,
        'args': (2, 3),
    }
}
