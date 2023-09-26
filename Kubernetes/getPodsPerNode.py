import json
import yaml
from collections import defaultdict
from prettytable import PrettyTable
from Kubernetes.utils import parse_memory, parse_cpu, run_command

def color_text(text, color_code):
    """Add ANSI color codes to text."""
    return f"\033[{color_code}m{text}\033[0m"

def get_node_capacity():
    nodes_output = run_command("kubectl get nodes -o json")
    nodes_json = json.loads(nodes_output)

    node_capacity = {}
    for node in nodes_json['items']:
        node_name = node['metadata']['name']
        cpu_capacity = parse_cpu(node['status']['capacity']['cpu'])
        memory_capacity = parse_memory(node['status']['capacity']['memory']) * 1024  # Assuming parse_memory returns GiB
        node_capacity[node_name] = {"cpu": cpu_capacity, "memory": memory_capacity}

    return node_capacity

def get_pods_per_node():
    node_capacity = get_node_capacity()

    pods_output = run_command("kubectl get pods --all-namespaces -o json")
    pods_json = json.loads(pods_output)

    pods_per_node = defaultdict(list)

    for pod in pods_json['items']:
        node_name = pod['spec'].get('nodeName')
        pod_name = pod['metadata']['name']
        namespace = pod['metadata']['namespace']

        if node_name:
            cpu_requests = 0
            memory_requests = 0
            containers = pod['spec']['containers']
            for container in containers:
                resources = container.get('resources', {})
                requests = resources.get('requests', {})
                cpu_requests += parse_cpu(requests.get('cpu', '0'))
                memory_requests += parse_memory(requests.get('memory', '0'))

            pods_per_node[node_name].append({
                "pod_name": pod_name,
                "namespace": namespace,
                "cpu_requests": cpu_requests,
                "memory_requests": memory_requests,
            })

    for node, pods in pods_per_node.items():
        table = PrettyTable()
        table.field_names = ["Node", "Namespace", "Pod", "CPURequests (cores)", "MemoryRequests (Mi)", "CDGC CPU % Utilization", "CDGC Mem % Utilization"]
        table.align = "l"

        selected_cpu = 0
        selected_memory = 0

        is_selected_namespace = any(pod['namespace'].startswith("ccgf") or pod['namespace'].startswith("idmcp") for pod in pods)

        for pod in pods:
            row = [
                node if pod is pods[0] else '',
                pod['namespace'],
                pod['pod_name'],
                f"{pod['cpu_requests']:.2f}",
                f"{int(pod['memory_requests'])}",
                '',
                ''
            ]

            if pod['namespace'].startswith("ccgf") or pod['namespace'].startswith("idmcp"):
                row = [color_text(cell, '32') for cell in row]  # 32 is the ANSI code for green
                selected_cpu += pod['cpu_requests']
                selected_memory += pod['memory_requests']

            table.add_row(row)

        cpu_utilization = f"{(selected_cpu / node_capacity[node]['cpu']) * 100:.2f}%"
        memory_utilization = f"{(selected_memory / node_capacity[node]['memory']) * 100:.2f}%"

        if is_selected_namespace:
            cpu_utilization = color_text(cpu_utilization, '32')
            memory_utilization = color_text(memory_utilization, '32')

        table.add_row(["", "Total", len(pods), "", "", cpu_utilization, memory_utilization])

        print(table)
        print()

import subprocess

def get_pods_per_all_clusters():
    with open('resources/NON-PROD_clusters.yaml', 'r') as file:
        clusters_data = yaml.safe_load(file)

    print("Clusters Data:", clusters_data)

    for cluster in clusters_data:
        config_command = cluster.get('config')
        if config_command:
            print(f"Executing config command: {config_command}")
            # Run the config command to set the kubeconfig context
            subprocess.run(config_command, shell=True, check=True)
            print("Fetching pods for the configured cluster:")
            get_pods_per_node()
            print()
        else:
            print("Config command not found in cluster:", cluster)

if __name__ == "__main__":
    get_pods_per_all_clusters()


