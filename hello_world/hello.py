"""Simple HTTP server used for demos and CI smoke tests.

Notes:
- Minimal demo server — not intended for production use.
- For production, run behind a WSGI server (gunicorn/uvicorn) and a reverse proxy.
- Do NOT expose repository files or secrets via these handlers.
- Optional integrations: Redis (set/get endpoints), Celery (enqueue/results), and
    HTTP checks (requires `requests`). These are only used if the corresponding
    Python packages are installed.
- Configuration:
    - `PORT` (env): port to bind (default: 8000)
    - `REDIS_HOST` (env): Redis hostname used by the Redis helper (default: "redis")

Endpoints provided (examples):
    - `GET /` or `GET /_health` -> 200 OK
    - `GET /redis-set?key=K&value=V` -> set key in Redis
    - `GET /redis-get?key=K` -> get key from Redis
    - `GET /task-add?a=1&b=2` -> enqueue Celery task (if available)
    - `GET /task-result?id=<task_id>` -> fetch Celery task result
    - `GET /check-nginx` -> simple HTTP check to service named `nginx` on the same network
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from urllib.parse import urlparse, parse_qs
import time
from typing import Optional

# Optional dependencies
try:
    import redis
except Exception:
    redis = None

try:
    import requests
except Exception:
    requests = None

# Celery (optional) — worker should run separately
try:
    from celery_app import add as celery_add
    from celery_app import celery as celery_instance
except Exception:
    celery_add = None
    celery_instance = None


# Port can be overridden with the PORT environment variable.
PORT = int(os.getenv("PORT", "8000"))


def _redis_client():
    if redis is None:
        return None
    try:
        return redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0, socket_connect_timeout=2)
    except Exception:
        return None


class Handler(BaseHTTPRequestHandler):
    """Handle a small set of endpoints used for healthchecks and testing.

    Endpoints implemented:
    - GET / or /_health : basic 200 response
    - GET /redis-set?key=K&value=V : set a key in Redis
    - GET /redis-get?key=K : get value from Redis
    - GET /task-add?a=1&b=2 : enqueue a Celery task (add)
    - GET /task-result?id=<task_id> : fetch Celery AsyncResult
    - GET /check-nginx : attempt an HTTP GET to service `nginx` on the compose network
    """

    def _write_text(self, text: str, code: int = 200) -> None:
        self.send_response(code)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        try:
            self.wfile.write(text.encode("utf-8"))
        except BrokenPipeError:
            # Peer closed connection (common when a reverse proxy times out or client disconnects).
            # Swallow this to avoid noisy traceback logs; no further action required.
            return
        except Exception as e:
            # Log unexpected write errors and continue.
            print(f"write error: {e}")
            return

    def do_HEAD(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path in ("/", "/_health"):
            return self._write_text("OK\n")

        if path == "/redis-set":
            key = qs.get("key", [None])[0]
            value = qs.get("value", [None])[0]
            if not key or value is None:
                return self._write_text("missing key or value\n", 400)
            r = _redis_client()
            if r is None:
                return self._write_text("redis client unavailable\n", 500)
            try:
                r.set(key, value)
                return self._write_text(f"OK set {key}\n")
            except Exception as e:
                return self._write_text(f"redis error: {e}\n", 500)

        if path == "/redis-get":
            key = qs.get("key", [None])[0]
            if not key:
                return self._write_text("missing key\n", 400)
            r = _redis_client()
            if r is None:
                return self._write_text("redis client unavailable\n", 500)
            try:
                v = r.get(key)
                return self._write_text(v.decode() + "\n" if v is not None else "(nil)\n")
            except Exception as e:
                return self._write_text(f"redis error: {e}\n", 500)

        if path == "/task-add":
            if celery_add is None:
                return self._write_text("celery not available in this process\n", 500)
            try:
                a = int(qs.get("a", [0])[0])
                b = int(qs.get("b", [0])[0])
            except Exception:
                return self._write_text("invalid args; use ?a=1&b=2\n", 400)
            try:
                res = celery_add.delay(a, b)
                return self._write_text(f"task_id:{res.id}\n")
            except Exception as e:
                return self._write_text(f"celery enqueue error: {e}\n", 500)

        if path == "/task-result":
            tid = qs.get("id", [None])[0]
            if not tid:
                return self._write_text("missing id\n", 400)
            if celery_instance is None:
                return self._write_text("celery not available in this process\n", 500)
            try:
                ar = celery_instance.AsyncResult(tid)
                state = ar.state
                result = ar.result
                return self._write_text(f"state:{state} result:{result}\n")
            except Exception as e:
                return self._write_text(f"celery result error: {e}\n", 500)

        if path == "/check-nginx":
            if requests is None:
                return self._write_text("requests not available in this process\n", 500)
            try:
                # Retry a few times to avoid transient DNS/connect hiccups.
                # Make attempts and timeout configurable via environment variables so
                # transient network issues can be tuned without changing code.
                attempts = int(os.getenv("CHECK_NGINX_ATTEMPTS", "3"))
                timeout = float(os.getenv("CHECK_NGINX_TIMEOUT", "5"))
                retry_delay = float(os.getenv("CHECK_NGINX_RETRY_DELAY", "0.5"))
                last_exc = None
                for attempt in range(1, attempts + 1):
                    try:
                        r = requests.get("http://nginx/", timeout=timeout)
                        return self._write_text(f"nginx status:{r.status_code}\n")
                    except Exception as e:
                        last_exc = e
                        if attempt < attempts:
                            time.sleep(retry_delay)
                return self._write_text(f"nginx check failed after {attempts} attempts: {last_exc}\n", 502)
            except Exception as e:
                return self._write_text(f"nginx check failed: {e}\n", 502)

        return self._write_text("Not Found\n", 404)


def run() -> None:
    server: HTTPServer = HTTPServer(("", PORT), Handler)
    print(f"Serving on port {PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()

