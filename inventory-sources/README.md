# Ansible AAP Inventory Sources

This directory contains inventory source configurations and development files for Ansible Automation Platform.

## Directory Structure
```
inventory-sources/
├── dynamic/          # Dynamic inventory scripts
├── static/           # Static inventory files
├── plugins/          # Custom inventory plugins
└── examples/         # Example configurations
```

## Getting Started

1. Activate the Python environment:
   ```bash
   source ../../python-venv/ansible-env/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r ../../python-venv/requirements.txt
   ```

3. Start AAP web interface:
   ```bash
   cd ../aap-installation
   ./setup.sh
   ```

4. Access AAP at: http://localhost:8080
   - Username: admin
   - Password: password

## Inventory Source Types Supported
- Static YAML/INI files
- Dynamic scripts (Python, shell)
- Cloud providers (AWS, Azure, GCP)
- Container platforms (Kubernetes, OpenShift)
- Custom inventory plugins