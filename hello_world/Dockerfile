FROM python:3.11-slim

# Working directory for the app
WORKDIR /app

# Install Python dependencies if provided. Use --no-cache-dir to keep image lean.
COPY requirements.txt ./
RUN if [ -f requirements.txt ]; then \
			python -m pip install --upgrade pip && \
			pip install --no-cache-dir -r requirements.txt; \
		fi

# Copy only application files. A .dockerignore at the repo root helps keep the context small.
COPY . .

# Container listens on this port by convention in this project
EXPOSE 8000

# NOTE: This image runs the app as the container default user (root in this base).
# For production images consider creating a dedicated non-root user and switching to it.
CMD ["python", "hello.py"]
