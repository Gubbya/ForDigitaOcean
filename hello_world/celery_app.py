import os
from celery import Celery

BROKER = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

celery = Celery("celery_app", broker=BROKER, backend=BACKEND)

@celery.task(name="celery_app.add")
def add(a, b):
    import os
    import time
    from celery import Celery

    try:
        import redis as redispy
    except Exception:
        redispy = None

    BROKER = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

    celery = Celery("celery_app", broker=BROKER, backend=BACKEND)


    @celery.task(name="celery_app.add")
    def add(a, b):
        try:
            return int(a) + int(b)
        except Exception:
            return None


    @celery.task(bind=True, name="celery_app.long_task")
    def long_task(self, total=5, delay=1):
        """Long-running demo task that publishes progress to Redis pub/sub.

        It publishes progress messages to channel `task-progress:<task_id>` as
        plain strings. If Redis is unavailable, the task still runs and returns
        when complete.
        """
        chan = f"task-progress:{self.request.id}"
        if redispy is None:
            for i in range(1, int(total) + 1):
                time.sleep(float(delay))
            return {"status": "no-redis", "task_id": self.request.id}

        r = redispy.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0)
        # publish incremental progress
        try:
            for i in range(1, int(total) + 1):
                time.sleep(float(delay))
                progress = int(i * 100 / int(total))
                msg = f"{{'task_id':'{self.request.id}','progress':{progress}}}"
                r.publish(chan, msg)
            r.publish(chan, "DONE")
        except Exception:
            # best-effort — ignore pub/sub failures
            pass
        return {"status": "completed", "task_id": self.request.id}


    # simple beat schedule for quick verification (every 30s)
    celery.conf.beat_schedule = {
        'periodic-add': {
            'task': 'celery_app.add',
            'schedule': 30.0,
            'args': (2, 3),
        }
    }
