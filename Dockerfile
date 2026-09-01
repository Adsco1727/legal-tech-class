FROM python:3.11.13-slim

WORKDIR /app

COPY setup.py ./
COPY dpo_system/ ./dpo_system/

RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir pytest

CMD ["python", "-m", "pytest", "-q", "dpo_system/tests/test_sec_intelligence.py"]
