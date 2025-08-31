#!/usr/bin/env python3
"""
Dynamic inventory script for network lab devices
Discovers devices and returns inventory in JSON format
"""

import json
import socket
import sys

def check_port(host, port):
    """Check if port is open on host"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def discover_devices():
    """Discover available network devices"""
    devices = {
        'ios': {'port': 2201, 'os': 'ios', 'type': 'router', 'vendor': 'cisco'},
        'iosxr': {'port': 2202, 'os': 'iosxr', 'type': 'router', 'vendor': 'cisco'},
        'nxos': {'port': 2203, 'os': 'nxos', 'type': 'switch', 'vendor': 'cisco'},
        'eos': {'port': 2204, 'os': 'eos', 'type': 'switch', 'vendor': 'arista'},
    }
    
    inventory = {
        '_meta': {'hostvars': {}},
        'all': {'children': ['network']},
        'network': {'children': []},
        'routers': {'hosts': []},
        'switches': {'hosts': []},
        'cisco': {'hosts': []},
        'arista': {'hosts': []}
    }
    
    for name, info in devices.items():
        if check_port('localhost', info['port']):
            hostname = f"{name}-device-01"
            
            # Add to appropriate groups
            inventory['network']['children'].append(name)
            inventory[name] = {'hosts': [hostname]}
            
            if info['type'] == 'router':
                inventory['routers']['hosts'].append(hostname)
            else:
                inventory['switches']['hosts'].append(hostname)
                
            inventory[info['vendor']]['hosts'].append(hostname)
            
            # Add host vars
            inventory['_meta']['hostvars'][hostname] = {
                'ansible_host': 'localhost',
                'ansible_port': info['port'],
                'ansible_user': 'root',
                'ansible_password': 'cisco123' if info['vendor'] == 'cisco' else 'arista123',
                'ansible_network_os': info['os'],
                'ansible_connection': 'network_cli',
                'device_type': info['type'],
                'vendor': info['vendor']
            }
    
    return inventory

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == '--list':
        print(json.dumps(discover_devices(), indent=2))
    elif len(sys.argv) == 3 and sys.argv[1] == '--host':
        print(json.dumps({}))
    else:
        print("Usage: {} --list | --host <hostname>".format(sys.argv[0]))
        sys.exit(1)
