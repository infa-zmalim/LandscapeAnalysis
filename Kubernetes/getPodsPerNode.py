import csv
import json
import subprocess
from collections import defaultdict

import yaml

from Kubernetes.utils import run_command, parse_memory, parse_cpu


def get_node_capacity():
    nodes_output = run_command("kubectl get nodes -o json")
    nodes_json = json.loads(nodes_output)

    node_capacity = {}
    for node in nodes_json['items']:
        node_name = node['metadata']['name']
        cpu_capacity = parse_cpu(node['status']['capacity']['cpu'])
        memory_capacity = parse_memory(node['status']['capacity']['memory'])
        node_capacity[node_name] = {"cpu": cpu_capacity, "memory": memory_capacity}

    return node_capacity


def get_pods_per_node(cluster_name, csv_writer):
    node_capacity = get_node_capacity()
    pods_output = run_command("kubectl get pods --all-namespaces -o json")
    pods_json = json.loads(pods_output)
    pods_per_node = defaultdict(list)

    for pod in pods_json['items']:
        node_name = pod['spec'].get('nodeName')
        if not node_name:
            continue
        if node_name not in node_capacity:
            print(f"Warning: Node {node_name} not found in node_capacity")
            continue

        pod_name = pod['metadata']['name']
        namespace = pod['metadata']['namespace']
        cpu_requests = sum(
            parse_cpu(container.get('resources', {}).get('requests', {}).get('cpu', '0')) for container in
            pod['spec']['containers'])
        memory_requests = sum(
            parse_memory(container.get('resources', {}).get('requests', {}).get('memory', '0')) for container in
            pod['spec']['containers'])

        pods_per_node[node_name].append({
            "pod_name": pod_name,
            "namespace": namespace,
            "cpu_requests": cpu_requests,
            "memory_requests": memory_requests,
        })

    for node, pods in pods_per_node.items():
        total_cpu = total_memory = selected_cpu = selected_memory = 0

        for pod in pods:
            if pod['namespace'].startswith(("ccgf", "idmcp", "gpt")):
                selected_cpu += pod['cpu_requests']
                selected_memory += pod['memory_requests']
            total_cpu += pod['cpu_requests']
            total_memory += pod['memory_requests']

            csv_writer.writerow({
                "Cluster": cluster_name,
                "Node": node,
                "Namespace": pod['namespace'],
                "Pod": pod['pod_name'],
                "CPURequests (cores)": f"{pod['cpu_requests']:.2f}",
                "MemoryRequests (Mi)": f"{int(pod['memory_requests'])}",
            })

        # Write total row to CSV for the current node
        selected_cpu_utilization = (selected_cpu / node_capacity[node]['cpu']) * 100
        selected_memory_utilization = (selected_memory / (1024 * node_capacity[node]['memory'])) * 100
        total_cpu_utilization = (total_cpu / node_capacity[node]['cpu']) * 100
        total_memory_utilization = (total_memory / (1024 * node_capacity[node]['memory'])) * 100

        csv_writer.writerow({
            "Cluster": cluster_name,
            "Node": node,
            "Namespace": "Total",
            "Pod": len(pods),
            "CPURequests (cores)": f"{total_cpu:.2f}",
            "MemoryRequests (Mi)": f"{int(total_memory)}",
            "CDGC CPU % Utilization": f"{selected_cpu_utilization:.2f}%",
            "CDGC Mem % Utilization": f"{selected_memory_utilization:.2f}%",
            "Total CPU % Utilization": f"{total_cpu_utilization:.2f}%",
            "Total Mem % Utilization": f"{total_memory_utilization:.2f}%",
        })


def get_pods_per_all_clusters():
    with open('resources/NON-PROD_clusters.yaml', 'r') as file:
        clusters_data = yaml.safe_load(file)

    fieldnames = [
        "Cluster", "Node", "Namespace", "Pod",
        "CPURequests (cores)", "MemoryRequests (Mi)",
        "CDGC CPU % Utilization", "CDGC Mem % Utilization",
        "Total CPU % Utilization", "Total Mem % Utilization"
    ]

    with open('Output/get_pods_per_all_clusters.csv', mode='w', newline='') as file:
        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
        csv_writer.writeheader()

        for cluster in clusters_data:
            cluster_name = cluster.get('name', 'Unknown Cluster')
            config_command = cluster.get('config')
            if config_command:
                try:
                    subprocess.run(config_command, shell=True, check=True)
                    get_pods_per_node(cluster_name, csv_writer)
                except subprocess.CalledProcessError as e:
                    print(f"Error running config command for cluster {cluster_name}: {e}")
            else:
                print("Config command not found in cluster:", cluster)


if __name__ == "__main__":
    get_pods_per_all_clusters()
