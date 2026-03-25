#!/usr/bin/env bash
# exit on error
set -o errexit

# Install backend dependencies
pip install -r requirements.txt

# Build frontend
cd frontend
npm install
npm run build
cd ..

# Create public directory and copy frontend build
mkdir -p public
cp -r frontend/dist/* public/
