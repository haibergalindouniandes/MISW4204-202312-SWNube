# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Configuration environment vars
ENV PYTHONUNBUFFERED True
ENV DB_HOST 34.66.39.220
ENV DB_NAME postgres
ENV DB_USER postgres
ENV DB_PASSWORD dbpass
ENV DB_PORT 5432
ENV SEPARATOR_SO /
ENV BUCKET_GOOGLE bucket-converter-web-app
ENV PATH_BUCKET_KEY misw4204-202312-swnube-bucket.json
ENV PATH_PUBSUB_KEY misw4204-202312-swnube-pub-sub.json
ENV PATH_TOPIC projects/misw4204-202312-swnube/topics/tasks-topic

# Update, upgrade system and install packages
RUN apt-get upgrade
RUN apt-get update
RUN apt-get install python3-dev -y
RUN apt-get install gcc -y
RUN apt-get install libc-dev -y
RUN apt-get install libffi-dev -y
RUN apt-get install libpq-dev -y

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install production dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app