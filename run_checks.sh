#!/bin/bash
set -e

echo "Running Frontend Build..."
cd frontend
npm run build
cd ..

echo "Running Backend Tests..."
source backend/venv/bin/activate
PYTHONPATH=. pytest
