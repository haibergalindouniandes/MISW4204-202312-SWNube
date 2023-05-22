# Start from python:3.8-alpine base image
FROM python:3.8-alpine
# Adding git, bash and openssh to the image
RUN apk update && apk upgrade && \
    apk add --no-cache bash git openssh \
    python3-dev \
    gcc \
    libc-dev \
    libffi-dev \
    libpq-dev \
    nfs-utils
# Make dir app
RUN mkdir /backend
WORKDIR /backend

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

COPY requirements.txt /backend/
RUN pip install -r requirements.txt
# Copy the source from the current directory to the Working Directory inside the container
COPY . .
# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app