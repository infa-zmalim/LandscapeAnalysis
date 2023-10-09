import json
import re
import subprocess
from collections import Counter

import yaml

from Kubernetes.config.config import Config

# You can easily switch between different configurations by changing the attribute here
config_file_path = Config.AWS_NON_PROD

with open(config_file_path, 'r') as file:
    clusters = yaml.safe_load(file)


def parse_memory(memory):
    if memory.endswith('Gi'):
        return float(memory.rstrip('Gi')) * 1024
    elif memory.endswith('G'):
        return float(memory.rstrip('G')) * 1024
    elif memory.endswith('Mi'):
        return float(memory.rstrip('Mi'))
    elif memory.endswith('M'):
        return float(memory.rstrip('M')) / 1024
    elif memory.endswith('Ki'):
        return float(memory.rstrip('Ki')) / (1024 ** 2)
    elif memory.endswith('K'):
        return float(memory.rstrip('K')) / (1024 ** 2)
    return float(memory)


def parse_cpu(cpu):
    if cpu.endswith('m'):
        return float(cpu.rstrip('m')) / 1000
    return float(cpu)


def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout
        return output.decode('utf-8')
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e.stderr.decode('utf-8')}")
        raise


def get_service_names(namespace):
    cmd_output = run_command(f"kubectl get deployment -n {namespace} -o json")
    deployments_data = json.loads(cmd_output)
    service_names = []

    for deployment in deployments_data['items']:
        replicas = deployment['spec'].get('replicas', 0)
        if replicas > 0:
            name = deployment['metadata']['name']
            name = re.split('-\d+', name)[0]
            service_names.append(name)

    counter = Counter(service_names)
    sorted_services = sorted(counter.items(), key=lambda x: x[1], reverse=True)
    return sorted_services

def get_deployments(namespace):
    """Fetch all deployments in a given namespace."""
    cmd_output = run_command(f"kubectl get deployments -n {namespace} -o json")
    return json.loads(cmd_output)

def get_hpas(namespace):
    """Fetch all HPAs in a given namespace."""
    cmd_output = run_command(f"kubectl get hpa -n {namespace} -o json")
    return json.loads(cmd_output)
