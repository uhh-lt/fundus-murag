# FUNDus! MuRAG

This repo contains the code for the FUNUus! MuRAG System -- a multimodal RAG-based Assistant to explore the FUNDus! database.

## Starting the system with Docker

### Prerequisites

#### Getting the data

_Note that this only works for LT and HCDS members. If you are not a member, you can request access to the data by contacting the [Florian Schneider](mailto:florian.schneider-1@uni-hamburg.de)._

1. Create a folder `data` in the root of the project
2. Copy the DataFrames from `/ltstorage/shares/projects/fundus-murag/data` to the `data` folder
3. Contact Florian Schneider to get the Google Service Acoount Credentials file and place it in the `data` folder (or create a new one with your Google Cloud account)

#### Setting up the environment

1. Navigate to the `docker` folder
2. Run `./setup-folders.sh` to create the necessary folders for the Docker volumes
3. Edit the `.env.example` file and save it as `.env` with the correct values

### Starting the Docker containers

1. Run `docker-compose pull` to pull the necessary images
2. Run `docker-compose up -d` to start the system
3. Run `docker-compose logs -f` to see the logs of the running containers