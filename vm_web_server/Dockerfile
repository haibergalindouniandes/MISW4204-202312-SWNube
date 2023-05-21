# Start from python:3.8-alpine base image
FROM python:3.8-alpine

# Allow statements and log messages to immediately appear in the Cloud Run logs
ENV PYTHONUNBUFFERED True

RUN apk update && apk upgrade && \
    apk add --no-cache bash git openssh \
    python3-dev \
    gcc \
    libc-dev \
    libffi-dev \
    libpq-dev \
    nfs-utils
# Copy application dependency manifests to the container image.
COPY requirements.txt ./

# Install production dependencies.
RUN pip install -r requirements.txt

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Run the web service on container startup.
# Use gunicorn webserver with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
