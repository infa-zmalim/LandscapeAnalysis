import json
from collections import defaultdict
from prettytable import PrettyTable
from Kubernetes.utils import parse_memory, parse_cpu, run_command


def color_text(text, color_code):
    """Add ANSI color codes to text."""
    return f"\033[{color_code}m{text}\033[0m"


def get_pods_per_node():
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
        table.field_names = ["Node", "Namespace", "Pod", "CPURequests (cores)", "MemoryRequests (Mi)"]
        table.align = "l"

        for pod in pods:
            row = [
                node if pod is pods[0] else '',
                pod['namespace'],
                pod['pod_name'],
                f"{pod['cpu_requests']:.2f}",
                f"{int(pod['memory_requests'])}"
            ]

            if pod['namespace'].startswith("ccgf") or pod['namespace'].startswith("idmcp"):
                row = [color_text(cell, '32') for cell in row]  # 32 is the ANSI code for green

            table.add_row(row)

        total_cpu = sum(pod['cpu_requests'] for pod in pods)
        total_memory = sum(pod['memory_requests'] for pod in pods)
        table.add_row(["", "Total", len(pods), f"{total_cpu:.2f}", f"{int(total_memory)}"])

        print(table)
        print()


if __name__ == "__main__":
    get_pods_per_node()
