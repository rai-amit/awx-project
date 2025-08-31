#!/usr/bin/env python3

"""
Test script for CMDB Orchestration
Simulates how CMDB would trigger incremental inventory updates in AWX
"""

import json
import requests
import base64

# AWX Configuration
AWX_URL = "http://localhost:8090"
AWX_USERNAME = "admin"
AWX_PASSWORD = "g4RePEc5mpYSPQJIwyzQUTKlIpW2SvyEq"

# Example: New devices from CMDB orchestration
new_devices = {
    "orchestration_data": {
        "devices": [
            {
                "name": "orchestrated-router-01",
                "vendor": "cisco",
                "device_type": "router", 
                "location": "datacenter1",
                "os_family": "ios",
                "mgmt_ip": "10.1.1.150",
                "ssh_port": 22,
                "ssh_user": "admin",
                "ssh_password": "cisco123",
                "model": "ISR4431",
                "serial_number": "FGL987654",
                "custom_region": "west",
                "custom_criticality": "high"
            },
            {
                "name": "orchestrated-switch-01", 
                "vendor": "arista",
                "device_type": "switch",
                "location": "datacenter2",
                "os_family": "eos",
                "mgmt_ip": "10.1.2.150",
                "ssh_port": 22,
                "ssh_user": "admin", 
                "ssh_password": "arista123",
                "model": "DCS-7050SX-64",
                "serial_number": "JPE654321",
                "custom_region": "east",
                "custom_criticality": "medium"
            }
        ]
    }
}

def trigger_incremental_sync(inventory_source_id, orchestration_data):
    """Trigger incremental inventory sync with new device data"""
    
    # Convert data to YAML format for source_vars
    import yaml
    source_vars_yaml = yaml.dump(orchestration_data, default_flow_style=False)
    
    # Update inventory source with new data
    auth_string = f"{AWX_USERNAME}:{AWX_PASSWORD}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {auth_b64}'
    }
    
    # Update source_vars with orchestration data
    patch_data = {
        "source_vars": source_vars_yaml
    }
    
    print(f"🔄 Updating inventory source {inventory_source_id} with orchestration data...")
    print(f"📊 Adding {len(orchestration_data['orchestration_data']['devices'])} new devices")
    
    # Update inventory source
    response = requests.patch(
        f"{AWX_URL}/api/v2/inventory_sources/{inventory_source_id}/",
        headers=headers,
        json=patch_data,
        timeout=30
    )
    
    if response.status_code == 200:
        print("✅ Inventory source updated")
        
        # Trigger sync
        sync_response = requests.post(
            f"{AWX_URL}/api/v2/inventory_sources/{inventory_source_id}/update/",
            headers=headers,
            timeout=30
        )
        
        if sync_response.status_code in [200, 201, 202]:
            sync_data = sync_response.json()
            print(f"🚀 Sync triggered - Job ID: {sync_data.get('id')}")
            return sync_data.get('id')
        else:
            print(f"❌ Sync failed: {sync_response.status_code} - {sync_response.text}")
            return None
    else:
        print(f"❌ Update failed: {response.status_code} - {response.text}")
        return None

def check_sync_status(job_id):
    """Check status of inventory sync job"""
    auth_string = f"{AWX_USERNAME}:{AWX_PASSWORD}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        'Authorization': f'Basic {auth_b64}'
    }
    
    response = requests.get(
        f"{AWX_URL}/api/v2/inventory_updates/{job_id}/",
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"📋 Job Status: {data.get('status')}")
        print(f"📋 Failed: {data.get('failed')}")
        print(f"📋 Finished: {data.get('finished')}")
        return data.get('status')
    else:
        print(f"❌ Status check failed: {response.status_code}")
        return None

if __name__ == "__main__":
    print("=== CMDB Orchestration Test ===")
    print("This simulates how CMDB orchestration triggers incremental inventory updates")
    print()
    
    # Note: You would need to create an incremental inventory source first
    # For now, this shows the data structure and API approach
    print("📋 Example orchestration data:")
    print(json.dumps(new_devices, indent=2))
    print()
    print("💡 To use:")
    print("1. Create inventory source with incremental-sync.yml")
    print("2. Call trigger_incremental_sync(source_id, new_devices)")
    print("3. Monitor sync progress with check_sync_status(job_id)")
    print()
    print("🔒 Safety Features:")
    print("- No device deletions allowed")
    print("- Preserves existing group memberships") 
    print("- Limits devices per sync batch")
    print("- Validates device data before processing")