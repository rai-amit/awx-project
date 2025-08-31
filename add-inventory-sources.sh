#!/bin/bash

# Add inventory sources to existing AWX inventory

AWX_URL="http://localhost:8090"
AWX_USERNAME="admin"
AWX_PASSWORD="g4RePOZmpYSPQJIwyzQUTKlIpW2SvyEq"
# Read IDs from config file
source .awx-config

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

echo "🔄 Creating Inventory Sources..."

# All Devices Source
echo "   Creating: All Network Devices"
awx_api POST "inventory_sources" '{
    "name": "All Network Devices",
    "description": "All devices from network lab",
    "inventory": '$INVENTORY_ID',
    "source": "scm", 
    "source_project": '$PROJECT_ID',
    "source_path": "inventory-sources/plugin-configs/all-devices.yml",
    "overwrite": true,
    "update_on_launch": true
}'

# Cisco Only Source  
echo "   Creating: Cisco Devices Only"
awx_api POST "inventory_sources" '{
    "name": "Cisco Devices Only",
    "description": "Cisco devices from network lab",
    "inventory": '$INVENTORY_ID',
    "source": "scm",
    "source_project": '$PROJECT_ID', 
    "source_path": "inventory-sources/plugin-configs/cisco-only.yml",
    "overwrite": true,
    "update_on_launch": true
}'

# Routers Only Source
echo "   Creating: Routers Only"
awx_api POST "inventory_sources" '{
    "name": "Routers Only", 
    "description": "Router devices from network lab",
    "inventory": '$INVENTORY_ID',
    "source": "scm",
    "source_project": '$PROJECT_ID',
    "source_path": "inventory-sources/plugin-configs/routers-only.yml", 
    "overwrite": true,
    "update_on_launch": true
}'

# Switches Only Source
echo "   Creating: Switches Only"
awx_api POST "inventory_sources" '{
    "name": "Switches Only",
    "description": "Switch devices from network lab", 
    "inventory": '$INVENTORY_ID',
    "source": "scm",
    "source_project": '$PROJECT_ID',
    "source_path": "inventory-sources/plugin-configs/switches-only.yml",
    "overwrite": true,
    "update_on_launch": true
}'

echo "✅ Inventory sources created!"
echo "💡 Go to AWX → Inventories → Network Devices Lab → Sources to sync"