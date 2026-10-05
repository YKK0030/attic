#!/usr/bin/env sh
set -eu

ollama pull all-minilm
ollama pull qwen2.5:0.5b-instruct
python3 -m pip install -r apps/api/requirements.txt
docker compose -f docker/docker-compose.yml up -d --build
