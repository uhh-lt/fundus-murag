#!/bin/bash
echo "Creating folders for the docker volumes"

if [ ! -d "weaviate-data" ]; then
  mkdir -v weaviate-data
else
  echo "weaviate-data already exists"
fi

if [ ! -d "fundus-murag-ui-logs" ]; then
  mkdir -v fundus-murag-ui-logs
else
  echo "fundus-murag-ui-logs already exists"
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