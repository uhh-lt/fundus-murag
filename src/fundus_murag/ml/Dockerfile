# syntax = docker/dockerfile:1.5
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-distutils \
    python3-pip \
    git \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

RUN python3 -m pip install --upgrade pip

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache \
    pip install -r requirements.txt
RUN --mount=type=cache,target=/root/.cache \
    pip install flash-attn==2.6.3

WORKDIR /app
COPY server.py .
COPY dto.py .

CMD ["python3", "server.py"]