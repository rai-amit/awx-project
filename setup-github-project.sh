#!/bin/bash

# Setup AWX project with GitHub repository

AWX_URL="http://localhost:8090"
AWX_USERNAME="admin"
AWX_PASSWORD="g4RePOZmpYSPQJIwyzQUTKlIpW2SvyEq"
GITHUB_REPO="https://github.com/rai-amit/awx-project.git"

# Function to make AWX API calls
awx_api() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    
    curl -s -X "$method" \
        -H "Content-Type: application/json" \
        -u "$AWX_USERNAME:$AWX_PASSWORD" \
        -d "$data" \
        "$AWX_URL/api/v2/$endpoint/"
}

echo "=== Setting up AWX Project with GitHub ==="

# Delete the old project if it exists
echo "🗑️  Cleaning up old project..."
curl -s -X DELETE -u "$AWX_USERNAME:$AWX_PASSWORD" "$AWX_URL/api/v2/projects/8/" || true

# Create new GitHub-based project
echo "📁 Creating GitHub project..."
PROJECT_DATA='{
    "name": "Network Lab Inventory (GitHub)",
    "description": "Network device lab inventory from GitHub",
    "organization": 1,
    "scm_type": "git",
    "scm_url": "'"$GITHUB_REPO"'",
    "scm_branch": "main",
    "scm_update_on_launch": true,
    "scm_update_cache_timeout": 0
}'

PROJECT_RESPONSE=$(awx_api POST "projects" "$PROJECT_DATA")
PROJECT_ID=$(echo "$PROJECT_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'id' in data:
        print(data['id'])
    else:
        print('Error:', data)
except Exception as e:
    print(f'Parse error: {e}')
")

echo "   ✅ Project created with ID: $PROJECT_ID"

# Wait for project sync
echo "⏳ Waiting for initial project sync..."
sleep 5

# Check project status
PROJECT_STATUS=$(curl -s -u "$AWX_USERNAME:$AWX_PASSWORD" "$AWX_URL/api/v2/projects/$PROJECT_ID/" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('status', 'unknown'))
except:
    print('error')
")

echo "   Project status: $PROJECT_STATUS"

if [ "$PROJECT_STATUS" = "successful" ]; then
    echo "✅ Project sync successful!"
    
    # Now create inventory and sources
    echo "📦 Creating inventory..."
    INVENTORY_DATA='{
        "name": "Network Devices Lab (GitHub)",
        "description": "Dynamic inventory from GitHub project",
        "organization": 1
    }'
    
    INVENTORY_RESPONSE=$(awx_api POST "inventories" "$INVENTORY_DATA")
    INVENTORY_ID=$(echo "$INVENTORY_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('id', ''))
except:
    print('')
")
    
    echo "   ✅ Inventory created with ID: $INVENTORY_ID"
    
    # Save IDs for next script
    echo "PROJECT_ID=$PROJECT_ID" > .awx-config
    echo "INVENTORY_ID=$INVENTORY_ID" >> .awx-config
    
    echo ""
    echo "🎉 Setup complete!"
    echo "💡 Next: Run ./add-inventory-sources.sh to add inventory sources"
    
else
    echo "❌ Project sync failed. Check:"
    echo "   1. GitHub repository is accessible"
    echo "   2. Repository contains the required files"
    echo "   3. AWX has internet access"
fi