import subprocess
import json
from collections import defaultdict

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if error and "No resources found" not in error.decode('utf-8'):
        raise Exception(error.decode('utf-8'))
    return output.decode('utf-8')

def get_pods_per_node():
    # Fetch all pods in all namespaces
    pods_output = run_command("kubectl get pods --all-namespaces -o json")
    pods_json = json.loads(pods_output)

    # Initialize a dictionary to hold the pod information per node
    pods_per_node = defaultdict(list)

    # Iterate over each pod and append it to the corresponding node list
    for pod in pods_json['items']:
        node_name = pod['spec'].get('nodeName')
        pod_name = pod['metadata']['name']
        namespace = pod['metadata']['namespace']

        if node_name:  # Only append pods that are assigned to a node
            pods_per_node[node_name].append({
                "pod_name": pod_name,
                "namespace": namespace,
            })

    # Print the result
    for node, pods in pods_per_node.items():
        print(f"Node: {node}")
        print(f"Pod Count: {len(pods)}")
        for pod in pods:
            print(f"  Namespace: {pod['namespace']}, PodName: {pod['pod_name']}")
        print()

if __name__ == "__main__":
    get_pods_per_node()
