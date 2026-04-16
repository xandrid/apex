#!/bin/bash

# APEX Backend Startup Script

echo "================================================"
echo "APEX Backend Startup"
echo "================================================"

# Add gcloud to PATH
export PATH="/Users/matthew/.gemini/antigravity/scratch/google-cloud-sdk/bin:$PATH"

# Check if authenticated
echo "Checking Google Cloud authentication..."
if ! gcloud auth application-default print-access-token &> /dev/null; then
    echo ""
    echo "⚠️  You need to authenticate with Google Cloud first."
    echo "Please run this command in your terminal:"
    echo ""
    echo "  /Users/matthew/.gemini/antigravity/scratch/google-cloud-sdk/bin/gcloud auth application-default login"
    echo ""
    echo "After logging in, run this script again."
    exit 1
fi

echo "✓ Authenticated"

# Check if .env has project ID set
if grep -q "your-gcp-project-id" .env 2>/dev/null; then
    echo ""
    echo "⚠️  Please edit the .env file and set your actual GCP Project ID"
    echo "File location: /Users/matthew/.gemini/antigravity/scratch/apex-app/backend/.env"
    echo ""
    exit 1
fi

echo "✓ Project ID configured"
echo ""
echo "Starting APEX Backend on http://localhost:8000"
echo "================================================"
echo ""

# Start the server
uvicorn app.main:app --reload
