# Network Lab Inventory Collection

This Ansible collection provides an inventory plugin for discovering network devices in the dockerized network lab environment.

## Installation

1. Copy this collection to your AWX project
2. Ensure the collection is in your `collections/` directory
3. Use the inventory plugin in your AWX inventory sources

## Usage

### Basic Discovery (All Devices)
```yaml
plugin: network_lab.inventory.network_devices
```

### Filtered Discovery Examples

**Cisco devices only:**
```yaml
plugin: network_lab.inventory.network_devices
filters:
  vendors:
    - cisco
```

**Routers only:**
```yaml
plugin: network_lab.inventory.network_devices
filters:
  device_types:
    - router
```

**Specific OS types:**
```yaml
plugin: network_lab.inventory.network_devices
filters:
  os_types:
    - ios
    - iosxr
```

## AWX Integration

1. Create a new Project in AWX pointing to your repository
2. Create a new Inventory Source with:
   - Source: Sourced from a Project
   - Project: Your project
   - Inventory file: `inventory-sources/plugin-configs/all-devices.yml`
3. Run inventory sync to discover devices

## Available Filters

- `os_types`: ios, iosxr, nxos, eos
- `device_types`: router, switch  
- `vendors`: cisco, arista