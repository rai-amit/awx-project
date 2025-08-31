#!/usr/bin/env python3

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
    name: network_devices
    plugin_type: inventory
    short_description: Network Device Lab Inventory Plugin
    description:
        - Dynamically discovers network devices from the dockerized lab environment
        - Supports filtering by OS type, device type, and vendor
        - Automatically configures connection parameters for network devices
    author:
        - Network Lab Team
    version_added: "1.0.0"
    options:
        plugin:
            description: Name of the plugin
            required: true
            choices: ['network_lab.inventory.network_devices']
        docker_host:
            description: Docker host to connect to
            type: str
            default: 'unix://var/run/docker.sock'
        network_name:
            description: Docker network name to scan for devices
            type: str
            default: 'network-lab_netlab'
        ssh_base_port:
            description: Base SSH port for device connections
            type: int
            default: 2201
        filters:
            description: Filters to apply when discovering devices
            type: dict
            default: {}
            suboptions:
                os_types:
                    description: List of OS types to include (ios, iosxr, nxos, eos)
                    type: list
                    elements: str
                    default: []
                device_types:
                    description: List of device types to include (router, switch)
                    type: list
                    elements: str
                    default: []
                vendors:
                    description: List of vendors to include (cisco, arista)
                    type: list
                    elements: str
                    default: []
        compose:
            description: Dictionary of vars to add to hosts
            type: dict
            default: {}
        keyed_groups:
            description: List of keys to create groups based on variables
            type: list
            elements: dict
            default: []
        groups:
            description: Dictionary of group names and host patterns
            type: dict
            default: {}
'''

EXAMPLES = r'''
# Basic usage - discover all devices
plugin: network_lab.inventory.network_devices

# Filter by OS types only
plugin: network_lab.inventory.network_devices
filters:
  os_types:
    - ios
    - iosxr

# Filter by device type and vendor
plugin: network_lab.inventory.network_devices
filters:
  device_types:
    - router
  vendors:
    - cisco

# Add custom variables and create groups
plugin: network_lab.inventory.network_devices
compose:
  ansible_ssh_common_args: '-o StrictHostKeyChecking=no'
  region: 'lab'
keyed_groups:
  - key: vendor
    prefix: vendor
  - key: device_type
    prefix: type
groups:
  production: false  # Mark all as non-production
'''

import json
import subprocess
import socket
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.errors import AnsibleError, AnsibleParserError


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    NAME = 'network_lab.inventory.network_devices'

    def __init__(self):
        super(InventoryModule, self).__init__()
        self.device_definitions = {
            'ios-router': {
                'hostname': 'ios-rtr-01',
                'os_type': 'ios',
                'device_type': 'router',
                'vendor': 'cisco',
                'model': 'CSR1000v',
                'ssh_port': 2201,
                'ssh_user': 'root',
                'ssh_password': 'cisco123',
                'mgmt_ip': '192.168.100.11'
            },
            'iosxr-router': {
                'hostname': 'iosxr-rtr-01',
                'os_type': 'iosxr',
                'device_type': 'router',
                'vendor': 'cisco',
                'model': 'ASR9k',
                'ssh_port': 2202,
                'ssh_user': 'root',
                'ssh_password': 'cisco123',
                'mgmt_ip': '192.168.100.12'
            },
            'nxos-switch': {
                'hostname': 'nxos-sw-01',
                'os_type': 'nxos',
                'device_type': 'switch',
                'vendor': 'cisco',
                'model': 'Nexus9000',
                'ssh_port': 2203,
                'ssh_user': 'root',
                'ssh_password': 'cisco123',
                'mgmt_ip': '192.168.100.13'
            },
            'eos-switch': {
                'hostname': 'eos-sw-01',
                'os_type': 'eos',
                'device_type': 'switch',
                'vendor': 'arista',
                'model': '7050SX',
                'ssh_port': 2204,
                'ssh_user': 'root',
                'ssh_password': 'arista123',
                'mgmt_ip': '192.168.100.14'
            }
        }

    def verify_file(self, path):
        """Return true/false if this is possibly a valid file for this plugin to consume"""
        valid = False
        if super(InventoryModule, self).verify_file(path):
            # Check if file contains our plugin name
            try:
                with open(path, 'r') as f:
                    content = f.read()
                    if 'network_lab.inventory.network_devices' in content:
                        valid = True
            except Exception:
                pass
        return valid

    def _is_container_running(self, container_name):
        """Check if a Docker container is running"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return container_name in result.stdout
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _is_port_accessible(self, host, port):
        """Check if SSH port is accessible"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    def _apply_filters(self, device_info, filters):
        """Apply filters to determine if device should be included"""
        if not filters:
            return True

        # Check OS type filter
        os_types = filters.get('os_types', [])
        if os_types and device_info['os_type'] not in os_types:
            return False

        # Check device type filter
        device_types = filters.get('device_types', [])
        if device_types and device_info['device_type'] not in device_types:
            return False

        # Check vendor filter
        vendors = filters.get('vendors', [])
        if vendors and device_info['vendor'] not in vendors:
            return False

        return True

    def parse(self, inventory, loader, path, cache=True):
        """Main parsing method"""
        super(InventoryModule, self).parse(inventory, loader, path, cache)

        # Read configuration
        config = self._read_config_data(path)
        
        # Get configuration options
        docker_host = self.get_option('docker_host')
        network_name = self.get_option('network_name')
        ssh_base_port = self.get_option('ssh_base_port')
        filters = self.get_option('filters') or {}
        compose_vars = self.get_option('compose') or {}
        keyed_groups = self.get_option('keyed_groups') or []
        groups = self.get_option('groups') or {}

        # Create base groups
        self.inventory.add_group('all')
        self.inventory.add_group('network')
        self.inventory.add_group('routers')
        self.inventory.add_group('switches')
        self.inventory.add_group('cisco')
        self.inventory.add_group('arista')
        self.inventory.add_group('ios')
        self.inventory.add_group('iosxr')
        self.inventory.add_group('nxos')
        self.inventory.add_group('eos')

        # Add network as child of all
        self.inventory.add_child('all', 'network')

        # Discover and add devices
        discovered_devices = 0
        for container_name, device_info in self.device_definitions.items():
            # Check if container is running
            if not self._is_container_running(f'network-{container_name}'):
                self.display.vvv(f"Container network-{container_name} not running, skipping")
                continue

            # Check if SSH port is accessible
            if not self._is_port_accessible('localhost', device_info['ssh_port']):
                self.display.vvv(f"SSH port {device_info['ssh_port']} not accessible, skipping {container_name}")
                continue

            # Apply filters
            if not self._apply_filters(device_info, filters):
                self.display.vvv(f"Device {container_name} filtered out by criteria")
                continue

            # Add host to inventory
            hostname = device_info['hostname']
            self.inventory.add_host(hostname)
            discovered_devices += 1

            # Set host variables
            host_vars = {
                'ansible_host': 'localhost',
                'ansible_port': device_info['ssh_port'],
                'ansible_user': device_info['ssh_user'],
                'ansible_password': device_info['ssh_password'],
                'ansible_network_os': device_info['os_type'],
                'ansible_connection': 'network_cli',
                'ansible_ssh_common_args': '-o StrictHostKeyChecking=no',
                'device_type': device_info['device_type'],
                'vendor': device_info['vendor'],
                'model': device_info['model'],
                'mgmt_ip': device_info['mgmt_ip'],
                'os_type': device_info['os_type'],
                'lab_container': f"network-{container_name}",
                'environment': 'lab'
            }

            # Apply composed variables
            if compose_vars:
                host_vars.update(compose_vars)

            # Set all host variables
            for var_name, var_value in host_vars.items():
                self.inventory.set_variable(hostname, var_name, var_value)

            # Add to appropriate groups
            self.inventory.add_child('network', hostname)
            
            # Add to OS-specific group
            os_group = device_info['os_type']
            if os_group not in self.inventory.groups:
                self.inventory.add_group(os_group)
            self.inventory.add_child(os_group, hostname)
            self.inventory.add_child('network', os_group)

            # Add to device type group
            device_type_group = f"{device_info['device_type']}s"
            if device_type_group not in self.inventory.groups:
                self.inventory.add_group(device_type_group)
            self.inventory.add_child(device_type_group, hostname)
            self.inventory.add_child('network', device_type_group)

            # Add to vendor group
            vendor_group = device_info['vendor']
            if vendor_group not in self.inventory.groups:
                self.inventory.add_group(vendor_group)
            self.inventory.add_child(vendor_group, hostname)
            self.inventory.add_child('network', vendor_group)

            self.display.vvv(f"Added device {hostname} ({device_info['os_type']})")

        # Apply keyed groups
        for group_def in keyed_groups:
            self._add_keyed_groups(group_def, host_vars)

        # Apply custom groups
        for group_name, group_expr in groups.items():
            self._add_custom_groups(group_name, group_expr)

        self.display.v(f"Network Lab Inventory: Discovered {discovered_devices} devices")

    def _add_keyed_groups(self, group_def, host_vars):
        """Add hosts to groups based on variable keys"""
        if 'key' not in group_def:
            return
        
        key = group_def['key']
        prefix = group_def.get('prefix', '')
        separator = group_def.get('separator', '_')
        
        for host in self.inventory.hosts:
            host_obj = self.inventory.hosts[host]
            if key in host_obj.vars:
                group_name = f"{prefix}{separator}{host_obj.vars[key]}" if prefix else str(host_obj.vars[key])
                self.inventory.add_group(group_name)
                self.inventory.add_child(group_name, host)

    def _add_custom_groups(self, group_name, group_expr):
        """Add custom groups based on expressions"""
        self.inventory.add_group(group_name)
        for host in self.inventory.hosts:
            # Simple evaluation - can be extended for complex expressions
            if isinstance(group_expr, bool) and group_expr:
                self.inventory.add_child(group_name, host)
            elif isinstance(group_expr, str):
                # Could implement expression evaluation here
                pass