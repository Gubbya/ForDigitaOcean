"""Simple HTTP server used for demos and CI smoke tests.

Notes:
- This is intentionally minimal and not suitable for production workloads.
- For production, run behind a real WSGI server (gunicorn/uvicorn) and optionally a reverse-proxy.
- Do NOT serve repository files or secrets from this handler.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from typing import Tuple


# Port can be overridden with the PORT environment variable.
PORT = int(os.getenv("PORT", "8000"))


class Handler(BaseHTTPRequestHandler):
    """Handle a minimal set of HTTP methods used by healthchecks and browsers.

    - GET: returns a small text response (200)
    - HEAD: same as GET but without body (200) — some health probes use HEAD
    Other methods will receive the default 501 response from BaseHTTPRequestHandler.
    """

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        # Keep the response tiny for quick healthchecks
        self.wfile.write(b"Hello, world!\n")

    def do_HEAD(self) -> None:
        # Some healthchecks/probes issue HEAD requests — respond 200 with no body
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()


def run() -> None:
    server: HTTPServer = HTTPServer(("", PORT), Handler)
    print(f"Serving on port {PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()

