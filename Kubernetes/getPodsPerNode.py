import json
import subprocess
from collections import defaultdict

import yaml
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
        memory_capacity = parse_memory(node['status']['capacity']['memory']) * 1024
        node_capacity[node_name] = {"cpu": cpu_capacity, "memory": memory_capacity}

    return node_capacity


def get_pods_per_node(cluster_name):
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
        table.field_names = ["Cluster", "Node", "Namespace", "Pod", "CPURequests (cores)", "MemoryRequests (Mi)",
                             "CDGC CPU % Utilization", "CDGC Mem % Utilization",
                             "Total CPU % Utilization", "Total Mem % Utilization"]
        table.align = "l"

        selected_cpu = 0
        selected_memory = 0
        total_cpu = 0
        total_memory = 0

        is_selected_namespace = any(
            pod['namespace'].startswith("ccgf") or pod['namespace'].startswith("idmcp") or pod['namespace'].startswith("gpt") for pod in pods)

        for pod in pods:
            row = [
                cluster_name if pod is pods[0] else '',
                node if pod is pods[0] else '',
                pod['namespace'],
                pod['pod_name'],
                f"{pod['cpu_requests']:.2f}",
                f"{int(pod['memory_requests'])}",
                '',
                '',
                '',
                ''
            ]

            if pod['namespace'].startswith("ccgf") or pod['namespace'].startswith("idmcp") or pod['namespace'].startswith("gpt"):
                row = [color_text(cell, '32') for cell in row]
                selected_cpu += pod['cpu_requests']
                selected_memory += pod['memory_requests']

            total_cpu += pod['cpu_requests']
            total_memory += pod['memory_requests']

            table.add_row(row)

        selected_cpu_utilization = f"{(selected_cpu / node_capacity[node]['cpu']) * 100:.2f}%"
        selected_memory_utilization = f"{(selected_memory / node_capacity[node]['memory']) * 100:.2f}%"
        total_cpu_utilization = f"{(total_cpu / node_capacity[node]['cpu']) * 100:.2f}%"
        total_memory_utilization = f"{(total_memory / node_capacity[node]['memory']) * 100:.2f}%"

        if is_selected_namespace:
            selected_cpu_utilization = color_text(selected_cpu_utilization, '32')
            selected_memory_utilization = color_text(selected_memory_utilization, '32')

        table.add_row([cluster_name, node, "Total", len(pods), f"{total_cpu:.2f}", f"{int(total_memory)}",
                       selected_cpu_utilization, selected_memory_utilization,
                       total_cpu_utilization, total_memory_utilization])

        print(table)
        print()


def get_pods_per_all_clusters():
    with open('resources/NON-PROD_clusters.yaml', 'r') as file:
        clusters_data = yaml.safe_load(file)
    for cluster in clusters_data:
        cluster_name = cluster.get('name', 'Unknown Cluster')
        config_command = cluster.get('config')
        if config_command:
            subprocess.run(config_command, shell=True, check=True)
            get_pods_per_node(cluster_name)
        else:
            print("Config command not found in cluster:", cluster)


if __name__ == "__main__":
    get_pods_per_all_clusters()
