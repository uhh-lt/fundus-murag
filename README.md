# CollEx

This repo contains the code for the CollEx System -- a multimodal RAG-based Assistant to explore the CollEx database.

## Starting the system in Production Mode

### Prerequisites

#### Getting the data

_Note that this only works for REDACTED members. If you are not a member, you can request access to the data by contacting [ANOYMIZED](mailto:anonymized@anonoymous.org)._

1. Create a folder `data` in the root of the project
2. Copy the DataFrames from `/ltstorage/shares/projects/fundus-murag/data` to the `data` folder
3. Contact Florian Schneider to get the Google Service Acoount Credentials file and place it in the `data` folder (or create a new one with your Google Cloud account)

#### Setting up the Production environment

1. Navigate to the `docker` folder
2. Run `./setup-folders.sh` to create the necessary folders for the Docker volumes
3. Edit the `.env.example` file and save it as `.env` with the modified values

### Starting the Docker containers

1. Run `docker compose pull` to pull the necessary images
2. Run `docker compose up -d` to start the system
3. Run `docker compose logs -f` to see the logs of the running containers

## Starting the system in Development Mode

### Prerequisites

1. Create a virtual environment with Python 3.10
2. Navigate to repository root
3. Install the requirements with `pip install -r requirements.txt`
4. Get the data as described in the [Docker](#getting-the-data) section
5. Navigate to the `docker` folder
6. Run `./setup-folders.sh` to create the necessary folders for the Docker volumes
7. Edit the `.env.dev.example` file and save it as `.env.dev` with the modified values
8. Navigate back to the repository root
9. Edit the `config/config.dev.example.yaml` file and save it as `config/config.dev.yaml` with the modified values

### (OPTIONAL) Starting the ML Service in Development Mode

You only need to do this if you want to run the ML service locally, e.g., to change the Embedding Model or add new functionality. Otherwise, skip this.

1. Navigate to repository root
2. In the `src/fundus_murag/ml/server.py` file, set the port to a random number (e.g., 23456)
3. Run `CUDA_VISIBLE_DEVICES=1 PYTHONPATH=src FUNDUS_ML_DEV_MODE=1 python src/fundus_murag/ml/server.py` to start the ML service in development mode
4. Check the logs to see on which port the service is running. You will need this port to start the MESOP application

### Starting the Docker Containers for Development

1. Navigate to the `docker` folder
2. (Optional) If you run the ML service in development mode, remove the `fundusml` profile from the `.env.dev`
3. Run `docker compose --env-file .env.dev up` in a `tmux` or similar shell to start the dev containers (i.e., Weaviate)
4. Run `curl http://localhost:<YOUR_FUNDUS_ML_EXPOSED_PORT>/embed` to check whether the CollEx ML Service is up and running. This should print sth. like `{"detail":"Method Not Allowed"}`

### Starting the CollEx Application for Development

1. Open the project in VS Code
2. Run the application as defined in the `launch.json`
