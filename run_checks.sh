#!/bin/bash
set -e

# Build the frontend
cd frontend
npm run build
cd ..

# Run backend tests
source backend/venv/bin/activate
export PYTHONPATH=.
pytest

# Final message
echo "All systems operational."