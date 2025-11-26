#!/usr/bin/env python3
"""Demo: submit `long_task` and listen for real-time progress via Redis pub/sub.

Usage (local/docker):
  - Ensure Redis + Celery worker are running (docker-compose provides services).
  - Run this script where it can reach Redis (e.g., in the same compose network or host
    with `REDIS_HOST` set).

Example:
  $ python hello_world/rt_demo.py

The script enqueues a `long_task` and listens on channel `task-progress:<task_id>`.
"""

import os
import time
import redis

try:
    from celery_app import long_task
except Exception as e:
    print("Failed importing celery_app.long_task:", e)
    raise


def main():
    host = os.getenv("REDIS_HOST", "redis")
    r = redis.Redis(host=host, port=6379, db=0, socket_connect_timeout=5)

    print("Submitting long_task (10 steps, 0.5s delay)")
    res = long_task.delay(10, 0.5)
    chan = f"task-progress:{res.id}"

    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(chan)
    print(f"Listening for progress on channel: {chan}")

    try:
        for message in pubsub.listen():
            if message is None:
                continue
            data = message.get('data')
            if isinstance(data, bytes):
                try:
                    data = data.decode()
                except Exception:
                    data = str(data)
            print(f"PUBSUB: {data}")
            if data == 'DONE' or (isinstance(data, str) and 'DONE' in data):
                break
    except KeyboardInterrupt:
        print("Interrupted, unsubscribing...")
    finally:
        pubsub.unsubscribe(chan)

    print("Fetching final result from Celery... (may block)")
    try:
        final = res.get(timeout=10)
        print("Result:", final)
    except Exception as e:
        print("Could not fetch result:", e)


if __name__ == '__main__':
    main()
