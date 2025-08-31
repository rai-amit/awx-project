#!/bin/bash

# Fix AWX project to work with local setup
# Options: 1) Use manual project type, 2) Set up simple git server, 3) Use volume mount

AWX_URL="http://localhost:8090"
AWX_USERNAME="admin"
AWX_PASSWORD="g4RePOZmpYSPQJIwyzQUTKlIpW2SvyEq"

echo "=== Fixing AWX Project Configuration ==="

# Delete the failed project
echo "🗑️  Deleting failed project..."
curl -s -X DELETE \
    -u "$AWX_USERNAME:$AWX_PASSWORD" \
    "$AWX_URL/api/v2/projects/8/"

# Create manual project (no SCM)
echo "📁 Creating manual project..."
PROJECT_DATA='{
    "name": "Network Lab Inventory (Manual)",
    "description": "Network device lab inventory - manual project type",
    "organization": 1,
    "scm_type": "",
    "local_path": ""
}'

PROJECT_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -u "$AWX_USERNAME:$AWX_PASSWORD" \
    -d "$PROJECT_DATA" \
    "$AWX_URL/api/v2/projects/")

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('id', ''))
except Exception as e:
    print(f'Error: {e}')
")

echo "   ✅ New Project ID: $PROJECT_ID"

echo ""
echo "💡 For manual project, you'll need to:"
echo "   1. Copy inventory files directly to AWX"
echo "   2. OR set up a simple Git server"
echo "   3. OR use different approach for local development"