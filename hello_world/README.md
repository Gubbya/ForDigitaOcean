# Hello World (Python)

Simple Hello World project in Python. This project is intentionally tiny
and used primarily for CI, container build, and deployment demonstrations.

Important notes
---------------
- This example app is a minimal HTTP server for demo and smoke-test purposes.
- Do not use this server directly in production; use a proper WSGI server and
	reverse proxy for performance, security and proper process management.
- Secrets (SSH keys, PATs) must never be committed to source; store them in
	GitHub Secrets and reference them in CI as shown in the repository workflow.

Run locally (PowerShell)
------------------------

```powershell
Set-Location -LiteralPath 'd:\digitalocean\ForDigitaOcean\hello_world'
python hello.py
```

Build Docker image locally
--------------------------

```powershell
# from repo root
docker build -f hello_world/Dockerfile -t fordigitaocean-hello:local hello_world
docker run -p 8000:8000 fordigitaocean-hello:local
```

CI / Deployment
---------------
This repository contains a GitHub Actions workflow (`.github/workflows/ci.yml`) that:
- runs basic static checks (flake8),
- builds a multi-arch image with `docker buildx`,
- optionally pushes to GHCR and deploys to a DigitalOcean droplet via SSH.

If you change deployment secrets or keys, rotate them and update GitHub Secrets.

Real-time demo (Redis + Celery)
--------------------------------
This repository includes a small demo that shows how a Celery task can publish
progress updates to Redis pub/sub and how a client can listen in real time.

Quick start (using `docker-compose` in the repo root):

```powershell
# start services (hello, redis, celery worker/beat)
docker-compose up -d redis celery-worker

# run the demo script from the host (ensure Python deps installed)
python .\hello_world\rt_demo.py
```

Notes:
- The demo publishes progress messages to channel `task-progress:<task_id>`.
- The demo script `hello_world/rt_demo.py` enqueues `long_task` and listens for updates.
- If you run inside Docker, ensure the script runs in the same network as the `redis` service
	(for example, by running it in the `hello` image or a helper container).

