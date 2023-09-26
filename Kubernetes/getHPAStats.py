import yaml
from Kubernetes.utils import run_command

# Load clusters from YAML file
with open('resources/AWS_NON-PROD_clusters.yaml', 'r') as file:
    clusters = yaml.safe_load(file)

def get_hpa(namespace):
    # Fetch HPAs from Kubernetes namespace
    cmd_output = run_command(f"kubectl get hpa -n {namespace}")

    # Check if cmd_output is not empty and split the output by lines
    lines = cmd_output.split('\n') if cmd_output else []

    # Skip the header and print the HPA details
    for line in lines[1:]:
        if line:
            print(line)

def main():
    for cluster in clusters:
        # Update kubeconfig for the cluster
        run_command(cluster["config"])

        # Fetch and display HPA details for each namespace in the cluster
        for namespace in cluster["namespaces"]:
            print(f"\n\nHPA details for namespace {namespace}:")
            get_hpa(namespace)

if __name__ == "__main__":
    main()
