# JSON Schema Validation for CMDB Orchestration

## Overview

The enhanced inventory plugin validates all incoming device data against a strict JSON schema to ensure data integrity and prevent inventory corruption.

## Validation Levels

### 1. JSON Schema Validation
- Validates overall data structure
- Ensures required fields are present
- Checks data types and formats
- Validates against `device-schema.json`

### 2. Individual Device Validation
- DNS-compliant hostname validation
- Enum validation for device_type, vendor, os_family
- IP address/hostname format validation
- SSH port range validation (1-65535)
- Custom field naming validation (must start with `custom_`)

### 3. Safety Validations
- Maximum device count per sync (default: 50)
- Deletion restriction checks
- Duplicate device name detection

## Required Device Fields

```json
{
  "name": "device-hostname",           // REQUIRED: DNS-compliant hostname
  "device_type": "router|switch|...",  // REQUIRED: Valid device type
  "vendor": "cisco|arista|...",        // REQUIRED: Valid vendor
  "mgmt_ip": "10.1.1.100"             // REQUIRED: IPv4/IPv6/hostname
}
```

## Supported Values

### Device Types
- `router`, `switch`, `firewall`, `load_balancer`, `wireless_controller`

### Vendors  
- `cisco`, `arista`, `juniper`, `fortinet`, `palo_alto`, `f5`, `mikrotik`

### OS Families
- `ios`, `iosxr`, `nxos`, `eos`, `junos`, `fortios`, `panos`

### Device Roles
- `core`, `distribution`, `access`, `edge`, `dmz`, `management`

## Validation Examples

### ✅ Valid Device Data
```json
{
  "orchestration_data": {
    "devices": [
      {
        "name": "rtr-core-01",
        "device_type": "router",
        "vendor": "cisco",
        "os_family": "ios",
        "location": "datacenter1",
        "mgmt_ip": "10.1.1.100",
        "ssh_port": 22,
        "ssh_user": "admin",
        "model": "ISR4431",
        "serial_number": "FGL123456",
        "roles": ["core", "edge"],
        "tags": ["production"],
        "custom_region": "west"
      }
    ]
  }
}
```

### ❌ Invalid Device Data Examples

**Missing Required Fields:**
```json
{
  "name": "incomplete-device",
  "device_type": "router"
  // Missing: vendor, mgmt_ip
}
```

**Invalid Device Type:**
```json
{
  "name": "bad-device",
  "device_type": "unknown_type",  // ❌ Not in allowed enum
  "vendor": "cisco",
  "mgmt_ip": "10.1.1.100"
}
```

**Invalid Hostname:**
```json
{
  "name": "device@with!invalid#chars",  // ❌ Special characters not allowed
  "device_type": "switch",
  "vendor": "cisco", 
  "mgmt_ip": "10.1.1.100"
}
```

**Invalid Custom Fields:**
```json
{
  "name": "device-01",
  "device_type": "router",
  "vendor": "cisco",
  "mgmt_ip": "10.1.1.100",
  "invalid_custom": "value",      // ❌ Must start with 'custom_'
  "custom_field": {"nested": {}}  // ❌ Must be scalar value
}
```

## Error Handling

### Schema Validation Errors
```
AnsibleError: Device data schema validation failed:
'unknown_type' is not one of ['router', 'switch', 'firewall', 'load_balancer', 'wireless_controller'] at path: orchestration_data.devices.0.device_type
```

### Individual Device Errors
```
Device validation failed:
Device 1 (rtr-01): Invalid device_type: unknown_type. Must be one of: ['router', 'switch', 'firewall', 'load_balancer', 'wireless_controller']
Device 2 (unnamed): Missing required field: name; Invalid mgmt_ip format: invalid.ip
```

### Safety Validation Errors
```
AnsibleError: Incremental sync exceeds maximum devices limit: 75 > 50
AnsibleError: Device deletion not allowed in safety mode: old-device-01
```

## CMDB Integration Best Practices

### 1. Pre-Validation in CMDB
```python
# Validate data before sending to AWX
def validate_before_send(device_data):
    required_fields = ['name', 'device_type', 'vendor', 'mgmt_ip']
    for device in device_data['devices']:
        for field in required_fields:
            if field not in device:
                raise ValueError(f"Missing {field} in {device}")
```

### 2. Error Handling in Orchestration
```python
try:
    job_id = trigger_incremental_sync(source_id, device_data)
    status = wait_for_completion(job_id)
    if status == 'failed':
        handle_validation_errors(job_id)
except Exception as e:
    log_orchestration_error(e)
    notify_ops_team(e)
```

### 3. Batch Processing
```python
# Process large device lists in batches
def process_device_batches(devices, batch_size=25):
    for i in range(0, len(devices), batch_size):
        batch = devices[i:i+batch_size]
        batch_data = {"orchestration_data": {"devices": batch}}
        trigger_incremental_sync(source_id, batch_data)
```

## Dependencies

### Required Python Libraries
```bash
pip install jsonschema  # For schema validation
pip install requests    # For CMDB API calls
pip install PyYAML     # For YAML processing
```

### AWX Requirements
- AWX/Tower 19.0+ 
- Python 3.8+ in execution environment
- Network connectivity to CMDB and devices

This validation framework ensures reliable, safe device data processing for your CMDB orchestration workflow!