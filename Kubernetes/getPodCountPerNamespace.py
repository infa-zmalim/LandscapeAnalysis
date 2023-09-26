import json

from Kubernetes.utils.utils import run_command, clusters


def get_running_pods_in_namespaces():
    for cluster in clusters:
        # Update kubeconfig for the current cluster
        run_command(cluster["config"])

        # Fetch all namespaces
        namespaces_output = run_command("kubectl get namespaces -o json")
        namespaces_json = json.loads(namespaces_output)

        # Iterate over each namespace
        for namespace_item in namespaces_json['items']:
            namespace_name = namespace_item['metadata']['name']

            # Get the number of running pods in the current namespace
            pods_output = run_command(f"kubectl get pods -n {namespace_name} --field-selector=status.phase==Running --no-headers")
            pod_count = len(pods_output.strip().split('\n')) if pods_output.strip() else 0

            # Output the cluster, namespace, and number of running pods
            print(f"Cluster: {cluster['config'].split('--name')[-1].strip()}, Namespace: {namespace_name}, Running Pods: {pod_count}")

if __name__ == "__main__":
    get_running_pods_in_namespaces()
