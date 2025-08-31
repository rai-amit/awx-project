#!/bin/bash

# AWX Project Setup Script
# Creates project and inventory sources for network device lab

set -e

# AWX Configuration
AWX_URL="http://localhost:8090"
AWX_USERNAME="admin"
AWX_PASSWORD="g4RePOZmpYSPQJIwyzQUTKlIpW2SvyEq"

# Project configuration
PROJECT_NAME="Network Lab Inventory"
PROJECT_SCM_TYPE="git"
PROJECT_SCM_URL="file:///Users/amkuma5/amkuma5/ansible-aap/awx-project"
INVENTORY_NAME="Network Devices Lab"

echo "=== Setting up AWX Project and Inventory ==="

# Function to make AWX API calls
awx_api() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    
    if [ "$method" = "POST" ]; then
        curl -s -X POST \
            -H "Content-Type: application/json" \
            -u "$AWX_USERNAME:$AWX_PASSWORD" \
            -d "$data" \
            "$AWX_URL/api/v2/$endpoint/"
    else
        curl -s -X GET \
            -u "$AWX_USERNAME:$AWX_PASSWORD" \
            "$AWX_URL/api/v2/$endpoint/"
    fi
}

# Get organization ID (usually 1 for Default)
echo "📋 Getting organization information..."
ORG_ID=$(awx_api GET "organizations" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['results'][0]['id'])
")
echo "   Organization ID: $ORG_ID"

# Create or update project
echo "📁 Creating AWX Project..."
PROJECT_DATA='{
    "name": "'"$PROJECT_NAME"'",
    "description": "Network device lab inventory and playbooks",
    "organization": '"$ORG_ID"',
    "scm_type": "'"$PROJECT_SCM_TYPE"'",
    "scm_url": "'"$PROJECT_SCM_URL"'",
    "scm_update_on_launch": true,
    "scm_update_cache_timeout": 0
}'

PROJECT_RESPONSE=$(awx_api POST "projects" "$PROJECT_DATA")
PROJECT_ID=$(echo "$PROJECT_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('id', ''))
except:
    print('')
")

if [ -z "$PROJECT_ID" ]; then
    echo "   ⚠️  Project may already exist or error occurred"
    PROJECT_ID=$(awx_api GET "projects" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for project in data['results']:
    if project['name'] == '$PROJECT_NAME':
        print(project['id'])
        break
")
fi

echo "   ✅ Project ID: $PROJECT_ID"

# Create inventory
echo "📦 Creating AWX Inventory..."
INVENTORY_DATA='{
    "name": "'"$INVENTORY_NAME"'",
    "description": "Dynamic inventory for network device lab",
    "organization": '"$ORG_ID"'
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

if [ -z "$INVENTORY_ID" ]; then
    echo "   ⚠️  Inventory may already exist"
    INVENTORY_ID=$(awx_api GET "inventories" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for inv in data['results']:
    if inv['name'] == '$INVENTORY_NAME':
        print(inv['id'])
        break
")
fi

echo "   ✅ Inventory ID: $INVENTORY_ID"

# Create inventory sources
declare -A SOURCES=(
    ["All Network Devices"]="inventory-sources/plugin-configs/all-devices.yml"
    ["Cisco Devices Only"]="inventory-sources/plugin-configs/cisco-only.yml"
    ["Routers Only"]="inventory-sources/plugin-configs/routers-only.yml"
    ["Switches Only"]="inventory-sources/plugin-configs/switches-only.yml"
    ["IOS Family Only"]="inventory-sources/plugin-configs/ios-family.yml"
)

echo "🔄 Creating Inventory Sources..."
for source_name in "${!SOURCES[@]}"; do
    source_file="${SOURCES[$source_name]}"
    echo "   Creating: $source_name"
    
    SOURCE_DATA='{
        "name": "'"$source_name"'",
        "description": "'"$source_name"' from network lab",
        "inventory": '"$INVENTORY_ID"',
        "source": "scm",
        "source_project": '"$PROJECT_ID"',
        "source_path": "'"$source_file"'",
        "overwrite": true,
        "update_on_launch": true,
        "update_cache_timeout": 0
    }'
    
    SOURCE_RESPONSE=$(awx_api POST "inventory_sources" "$SOURCE_DATA")
    SOURCE_ID=$(echo "$SOURCE_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('id', 'Error'))
except:
    print('Parse Error')
")
    echo "     ✅ Source ID: $SOURCE_ID"
done

echo ""
echo "🎉 AWX Project Setup Complete!"
echo ""
echo "📋 Summary:"
echo "   Project: $PROJECT_NAME (ID: $PROJECT_ID)"
echo "   Inventory: $INVENTORY_NAME (ID: $INVENTORY_ID)"
echo "   Repository: $PROJECT_SCM_URL"
echo ""
echo "🌐 Access AWX at: $AWX_URL"
echo "👤 Username: $AWX_USERNAME"
echo "🔑 Password: $AWX_PASSWORD"
echo ""
echo "💡 Next steps:"
echo "   1. Go to Projects and sync '$PROJECT_NAME'"
echo "   2. Go to Inventories → '$INVENTORY_NAME' → Sources"
echo "   3. Sync each inventory source to import devices"