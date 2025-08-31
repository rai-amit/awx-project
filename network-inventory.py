#!/usr/bin/env python3

import json
import subprocess
import socket
import sys
import argparse

class NetworkInventory:
    def __init__(self):
        self.inventory = {}
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

    def _is_container_running(self, container_name):
        """Check if Docker container is running"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
                capture_output=True, text=True, timeout=10
            )
            return container_name in result.stdout
        except:
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

        # Check vendor filter (for Cisco-only filtering)
        if 'cisco_only' in filters and filters['cisco_only']:
            return device_info['vendor'] == 'cisco'
            
        # Check device type filter
        if 'device_types' in filters:
            return device_info['device_type'] in filters['device_types']
            
        # Check OS type filter
        if 'os_types' in filters:
            return device_info['os_type'] in filters['os_types']

        return True

    def get_inventory(self, filters=None):
        """Generate inventory JSON"""
        # Initialize inventory structure
        self.inventory = {
            '_meta': {'hostvars': {}},
            'all': {'children': ['network']},
            'network': {'children': [], 'hosts': []},
            'routers': {'hosts': []},
            'switchs': {'hosts': []},
            'cisco': {'hosts': []},
            'arista': {'hosts': []},
            'ios': {'hosts': []},
            'iosxr': {'hosts': []},
            'nxos': {'hosts': []},
            'eos': {'hosts': []}
        }

        # Discover devices
        for container_name, device_info in self.device_definitions.items():
            # Check if container is running
            if not self._is_container_running(f'network-{container_name}'):
                continue

            # Check if SSH port is accessible
            if not self._is_port_accessible('localhost', device_info['ssh_port']):
                continue

            # Apply filters
            if not self._apply_filters(device_info, filters):
                continue

            hostname = device_info['hostname']
            
            # Add host variables
            self.inventory['_meta']['hostvars'][hostname] = {
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

            # Add to groups
            self.inventory['network']['hosts'].append(hostname)
            self.inventory[device_info['device_type'] + 's']['hosts'].append(hostname)
            self.inventory[device_info['vendor']]['hosts'].append(hostname)
            self.inventory[device_info['os_type']]['hosts'].append(hostname)

            # Add OS group to network children if not already there
            if device_info['os_type'] not in self.inventory['network']['children']:
                self.inventory['network']['children'].append(device_info['os_type'])

        return self.inventory

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true', help='List all hosts')
    parser.add_argument('--host', help='Get variables for specific host')
    parser.add_argument('--cisco-only', action='store_true', help='Only Cisco devices')
    parser.add_argument('--routers-only', action='store_true', help='Only router devices')
    parser.add_argument('--switches-only', action='store_true', help='Only switch devices')
    
    args = parser.parse_args()
    
    inventory = NetworkInventory()
    
    if args.list:
        filters = {}
        if args.cisco_only:
            filters['cisco_only'] = True
        elif args.routers_only:
            filters['device_types'] = ['router']
        elif args.switches_only:
            filters['device_types'] = ['switch']
            
        result = inventory.get_inventory(filters)
        print(json.dumps(result, indent=2))
    elif args.host:
        # AWX might request specific host info
        print(json.dumps({}))
    else:
        parser.print_help()

if __name__ == '__main__':
    main()