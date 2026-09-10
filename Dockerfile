FROM python:3.12-slim

# Unbuffered output so log lines appear immediately in `docker logs`,
# and no .pyc files written into the image.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first so this layer stays cached when only code changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./
COPY utils/ ./utils/
COPY config_example.ini ./

# The app binds privileged ports (22, 23, 139, ...), so it runs as root inside
# the container. If you only listen on ports above 1024, create an unprivileged
# user here and switch to it with `USER`.
#
# NOTE: There is intentionally no HEALTHCHECK. Probing a listening port would
# create a fake connection attempt that gets reported to AbuseIPDB.

# Documentation only; with `network_mode: host` these are not published.
EXPOSE 22 23 139 445 1433 1434 3306 5432 8080 8291 8443

# Exec form so Python is PID 1 and receives SIGTERM for the graceful-shutdown handler.
CMD ["python3", "main.py"]
