#!/usr/bin/env python3

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
    name: cmdb_orchestration
    plugin_type: inventory
    short_description: CMDB Orchestration Inventory Plugin
    description:
        - Supports both full CMDB sync and incremental updates via JSON data
        - Processes device data using configurable filters and group mappings
        - Incremental mode only adds/updates devices, never deletes
        - Designed for CMDB orchestration workflows
    author:
        - Network Lab Team
    version_added: "1.0.0"
    options:
        plugin:
            description: Name of the plugin
            required: true
            choices: ['network_lab.inventory.cmdb_orchestration']
        sync_mode:
            description: Synchronization mode
            type: str
            choices: ['full_sync', 'incremental']
            default: 'full_sync'
        cmdb_endpoint:
            description: CMDB API endpoint for full sync
            type: str
            required: false
        direct_data:
            description: Direct JSON data for incremental sync (passed via source_vars)
            type: dict
            required: false
        filters:
            description: Device filtering criteria
            type: dict
            default: {}
            suboptions:
                device_types:
                    description: List of device types to include
                    type: list
                    elements: str
                    default: []
                vendors:
                    description: List of vendors to include
                    type: list
                    elements: str
                    default: []
                locations:
                    description: List of locations to include
                    type: list
                    elements: str
                    default: []
                os_families:
                    description: List of OS families to include
                    type: list
                    elements: str
                    default: []
        group_mappings:
            description: Group creation mappings
            type: dict
            default: {}
            suboptions:
                by_vendor:
                    description: Create groups by vendor
                    type: bool
                    default: true
                by_location:
                    description: Create groups by location
                    type: bool
                    default: true
                by_device_type:
                    description: Create groups by device type
                    type: bool
                    default: true
                by_os_family:
                    description: Create groups by OS family
                    type: bool
                    default: true
                custom_groups:
                    description: Custom group definitions
                    type: dict
                    default: {}
        safety_mode:
            description: Safety restrictions for incremental updates
            type: dict
            default: {}
            suboptions:
                allow_deletions:
                    description: Allow device deletions in incremental mode
                    type: bool
                    default: false
                preserve_existing_groups:
                    description: Preserve existing group memberships
                    type: bool
                    default: true
                max_devices_per_sync:
                    description: Maximum devices to process in one sync
                    type: int
                    default: 100
'''

EXAMPLES = r'''
# Full CMDB sync (existing behavior)
plugin: network_lab.inventory.cmdb_orchestration
sync_mode: full_sync
cmdb_endpoint: "https://cmdb.company.com/api/devices"
filters:
  device_types: ["router", "switch"]
  vendors: ["cisco", "arista"]
group_mappings:
  by_vendor: true
  by_location: true

# Incremental sync via CMDB orchestration
plugin: network_lab.inventory.cmdb_orchestration
sync_mode: incremental
direct_data:
  devices:
    - name: "new-router-01"
      vendor: "cisco"
      device_type: "router"
      location: "datacenter1"
      os_family: "ios"
      mgmt_ip: "10.1.1.100"
      ssh_port: 22
    - name: "new-switch-01"
      vendor: "arista"
      device_type: "switch"
      location: "datacenter2"
      os_family: "eos"
      mgmt_ip: "10.1.2.100"
      ssh_port: 22
filters:
  device_types: ["router", "switch"]
group_mappings:
  by_vendor: true
  by_location: true
safety_mode:
  allow_deletions: false
  preserve_existing_groups: true
  max_devices_per_sync: 50
'''

import json
import requests
import yaml
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.errors import AnsibleError, AnsibleParserError


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    NAME = 'network_lab.inventory.cmdb_orchestration'

    def verify_file(self, path):
        """Return true/false if this is possibly a valid file for this plugin to consume"""
        valid = False
        if super(InventoryModule, self).verify_file(path):
            try:
                with open(path, 'r') as f:
                    content = f.read()
                    if 'network_lab.inventory.cmdb_orchestration' in content:
                        valid = True
            except Exception:
                pass
        return valid

    def _fetch_from_cmdb(self, endpoint):
        """Fetch device data from CMDB API"""
        try:
            response = requests.get(endpoint, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise AnsibleError(f"Failed to fetch from CMDB: {e}")

    def _apply_filters(self, device, filters):
        """Apply filters to determine if device should be included"""
        if not filters:
            return True

        # Device type filter
        device_types = filters.get('device_types', [])
        if device_types and device.get('device_type') not in device_types:
            return False

        # Vendor filter  
        vendors = filters.get('vendors', [])
        if vendors and device.get('vendor') not in vendors:
            return False

        # Location filter
        locations = filters.get('locations', [])
        if locations and device.get('location') not in locations:
            return False

        # OS family filter
        os_families = filters.get('os_families', [])
        if os_families and device.get('os_family') not in os_families:
            return False

        return True

    def _validate_incremental_safety(self, devices, safety_config):
        """Validate incremental update safety restrictions"""
        max_devices = safety_config.get('max_devices_per_sync', 100)
        
        if len(devices) > max_devices:
            raise AnsibleError(f"Incremental sync exceeds maximum devices limit: {len(devices)} > {max_devices}")

        # Check for deletion attempts (devices with _state: absent)
        allow_deletions = safety_config.get('allow_deletions', False)
        if not allow_deletions:
            for device in devices:
                if device.get('_state') == 'absent':
                    raise AnsibleError(f"Device deletion not allowed in safety mode: {device.get('name')}")

        return True

    def _create_device_groups(self, device, group_mappings):
        """Create and return groups for a device based on mappings"""
        groups = []

        if group_mappings.get('by_vendor', True) and device.get('vendor'):
            groups.append(f"vendor_{device['vendor']}")

        if group_mappings.get('by_location', True) and device.get('location'):
            groups.append(f"location_{device['location']}")

        if group_mappings.get('by_device_type', True) and device.get('device_type'):
            groups.append(f"type_{device['device_type']}")

        if group_mappings.get('by_os_family', True) and device.get('os_family'):
            groups.append(f"os_{device['os_family']}")

        # Add custom groups
        custom_groups = group_mappings.get('custom_groups', {})
        for group_name, group_criteria in custom_groups.items():
            if self._matches_criteria(device, group_criteria):
                groups.append(group_name)

        return groups

    def _matches_criteria(self, device, criteria):
        """Check if device matches custom group criteria"""
        for key, value in criteria.items():
            if device.get(key) != value:
                return False
        return True

    def _ensure_group_exists(self, group_name):
        """Ensure group exists in inventory"""
        if group_name not in self.inventory.groups:
            self.inventory.add_group(group_name)

    def _add_device_to_inventory(self, device, group_mappings, preserve_existing):
        """Add or update a single device in inventory"""
        hostname = device['name']
        
        # Check if host already exists
        host_exists = hostname in self.inventory.hosts
        if host_exists and preserve_existing:
            self.display.vvv(f"Host {hostname} already exists, updating variables only")
        
        # Add host to inventory
        self.inventory.add_host(hostname)

        # Set host variables
        host_vars = {
            'ansible_host': device.get('mgmt_ip', device.get('ansible_host')),
            'ansible_port': device.get('ssh_port', device.get('ansible_port', 22)),
            'ansible_user': device.get('ssh_user', device.get('ansible_user', 'admin')),
            'ansible_password': device.get('ssh_password', device.get('ansible_password')),
            'ansible_network_os': device.get('os_family', device.get('ansible_network_os')),
            'ansible_connection': 'network_cli',
            'ansible_ssh_common_args': '-o StrictHostKeyChecking=no',
            
            # Device metadata
            'device_type': device.get('device_type'),
            'vendor': device.get('vendor'),
            'location': device.get('location'),
            'os_family': device.get('os_family'),
            'model': device.get('model'),
            'serial_number': device.get('serial_number'),
            'mgmt_ip': device.get('mgmt_ip'),
            
            # Orchestration metadata
            'sync_mode': 'incremental' if not host_exists else 'updated',
            'last_updated': device.get('last_updated'),
            'source': 'cmdb_orchestration'
        }

        # Add custom variables from device data
        for key, value in device.items():
            if key.startswith('custom_'):
                host_vars[key] = value

        # Set variables
        for var_name, var_value in host_vars.items():
            if var_value is not None:
                self.inventory.set_variable(hostname, var_name, var_value)

        # Create and assign groups
        device_groups = self._create_device_groups(device, group_mappings)
        
        for group_name in device_groups:
            self._ensure_group_exists(group_name)
            self.inventory.add_child(group_name, hostname)

        # Add to base network group
        self._ensure_group_exists('network')
        self.inventory.add_child('network', hostname)

        self.display.vvv(f"Processed device: {hostname} in mode: {'update' if host_exists else 'add'}")

    def parse(self, inventory, loader, path, cache=True):
        """Main parsing method"""
        super(InventoryModule, self).parse(inventory, loader, path, cache)

        # Read configuration
        config = self._read_config_data(path)
        
        # Get configuration options
        sync_mode = self.get_option('sync_mode')
        cmdb_endpoint = self.get_option('cmdb_endpoint')
        direct_data = self.get_option('direct_data') or {}
        filters = self.get_option('filters') or {}
        group_mappings = self.get_option('group_mappings') or {}
        safety_mode = self.get_option('safety_mode') or {}

        self.display.v(f"CMDB Orchestration Plugin - Mode: {sync_mode}")

        # Get device data based on mode
        if sync_mode == 'full_sync':
            if not cmdb_endpoint:
                raise AnsibleError("cmdb_endpoint required for full_sync mode")
            
            self.display.v(f"Full sync from CMDB: {cmdb_endpoint}")
            cmdb_response = self._fetch_from_cmdb(cmdb_endpoint)
            devices = cmdb_response.get('devices', [])
            
        elif sync_mode == 'incremental':
            self.display.v("Incremental sync with direct data")
            
            # Try to get data from source_vars (AWX API call)
            source_vars = getattr(self, '_source_vars', {})
            if source_vars and 'orchestration_data' in source_vars:
                devices = source_vars['orchestration_data'].get('devices', [])
            elif direct_data and 'devices' in direct_data:
                devices = direct_data['devices']
            else:
                devices = []
                
            if not devices:
                self.display.warning("No incremental data provided - skipping sync")
                return

            # Apply safety validations for incremental mode
            self._validate_incremental_safety(devices, safety_mode)
            
        else:
            raise AnsibleError(f"Invalid sync_mode: {sync_mode}")

        # Process devices
        self.display.v(f"Processing {len(devices)} devices")
        processed_count = 0
        skipped_count = 0

        for device in devices:
            # Validate required fields
            if not device.get('name'):
                self.display.warning(f"Device missing name field, skipping: {device}")
                skipped_count += 1
                continue

            # Apply filters
            if not self._apply_filters(device, filters):
                self.display.vvv(f"Device {device['name']} filtered out")
                skipped_count += 1
                continue

            # Add device to inventory
            try:
                preserve_existing = safety_mode.get('preserve_existing_groups', True)
                self._add_device_to_inventory(device, group_mappings, preserve_existing)
                processed_count += 1
                
            except Exception as e:
                self.display.warning(f"Failed to process device {device['name']}: {e}")
                skipped_count += 1

        # Summary
        self.display.v(f"CMDB Orchestration completed: {processed_count} processed, {skipped_count} skipped")

        # Set inventory metadata
        self.inventory.set_variable('all', 'sync_metadata', {
            'sync_mode': sync_mode,
            'processed_devices': processed_count,
            'skipped_devices': skipped_count,
            'sync_timestamp': self._get_timestamp(),
            'safety_restrictions': {
                'deletions_allowed': safety_mode.get('allow_deletions', False),
                'preserve_existing': safety_mode.get('preserve_existing_groups', True)
            }
        })

    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'