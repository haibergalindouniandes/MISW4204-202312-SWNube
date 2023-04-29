# Start from python:3.8-alpine base image
FROM python:3.11-buster
# Adding git, bash and openssh to the image
RUN set -e; \
    apt-get update -y && apt-get install -y \
    python3-dev \
    gcc \
    libc-dev \
    libffi-dev \
    libpq-dev \    
    lsb-release; \
    gcsFuseRepo=gcsfuse-`lsb_release -c -s`; \
    echo "deb https://packages.cloud.google.com/apt $gcsFuseRepo main" | \
    sudo tee /etc/apt/sources.list.d/gcsfuse.list; \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    sudo apt-key add -; \
    apt-get update; \
    apt-get install -y fuse gcsfuse \
    && apt-get clean
#Login GCP
RUN gcloud auth application-default login --no-launch-browser -y 4/0AbUR2VP4hadLMUKbRFGJ2DwPMh27Lg7kSPidLc66TGE34RiOwHf_3vdkxQHL9LfKAF0Eqw 

# Make dir nfs
RUN mkdir -p /home/misw-cloud-storage
# Montaje de la ruta
RUN gcsfuse misw-cloud-storage "/home/misw-cloud-storage"
# Make dir app
RUN mkdir /backend
WORKDIR /backend

COPY requirements.txt /backend/
RUN pip install -r requirements.txt
# Copy the source from the current directory to the Working Directory inside the container
COPY . .

# Expose port 8080 to the outside world
EXPOSE 5000