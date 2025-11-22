FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN if [ -f requirements.txt ]; then python -m pip install --upgrade pip && pip install -r requirements.txt; fi

COPY . .

CMD ["python", "hello.py"]
