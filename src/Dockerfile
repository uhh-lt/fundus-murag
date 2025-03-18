# syntax = docker/dockerfile:1.5
FROM python:3.10.14-bullseye

RUN apt-get update && \
    apt-get install -y \
    # General dependencies
    locales \
    locales-all && \
    # Clean local repository of package files since they won't be needed anymore.
    # Make sure this line is called after all apt-get update/install commands have
    # run.
    apt-get clean && \
    # Also delete the index files which we also don't need anymore.
    rm -rf /var/lib/apt/lists/*

ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US.UTF-8

# Install dependencies
WORKDIR /code

RUN --mount=type=cache,target=/root/.cache \
    pip install uv
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache \
    uv pip install -r requirements.txt --system

COPY fundus_murag /code/fundus_murag

CMD ["fastapi", "run", "fundus_murag/main.py", "--host", "0.0.0.0", "--port", "8000"]
