#!/bin/bash
echo "Creating folders for the docker volumes"

if [ ! -d "weaviate_data" ]; then
  mkdir -v weaviate_data
else
  echo "weaviate_data already exists"
fi

if [ ! -d "weaviate_data-dev" ]; then
  mkdir -v weaviate_data-dev
else
  echo "weaviate_data-dev already exists"
fi

if [ ! -d "fundus-murag-backend-logs" ]; then
  mkdir -v fundus-murag-backend-logs
else
  echo "fundus-murag-backend-logs already exists"
fi

if [ ! -d "models_cache" ]; then
  mkdir -v models_cache
else
  echo "models_cache already exists"
fi

if [ ! -d "cache" ]; then
  mkdir -v cache
else
  echo "cache already exists"
fi

if [ ! -d "templates" ]; then
  mkdir -v templates
else
  echo "templates already exists"
fi

if [ ! -d "mlflow_runs" ]; then
  mkdir -v mlflow_runs
else
  echo "mlflow_runs already exists"
fi

if [ ! -d "mlflow_artifacts" ]; then
  mkdir -v mlflow_artifacts
else
  echo "mlflow_artifacts already exists"
fi
