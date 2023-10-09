import subprocess
import json

from Kubernetes.utils.utils import clusters, run_command

def getDeploymentsWithNoHpa(NameSpace):
    # Equivalent to kubectl get deployments command
    cmd_output = subprocess.getoutput(f"kubectl get deployments -n {NameSpace} -o json")
    deployments = json.loads(cmd_output)

    print(f"\nDeployments with no HPA in namespace {NameSpace}:\n")
    for deployment in deployments["items"]:
        deploymentName = deployment["metadata"]["name"]
        if NameSpace not in deploymentName:
            hpaExists = subprocess.getoutput(f"kubectl get hpa {deploymentName}-hpa -n {NameSpace} -o name --ignore-not-found")
            if not hpaExists:
                print(deploymentName)

if __name__ == "__main__":
    for cluster in clusters:
        # Set kubeconfig for the cluster
        run_command(cluster["config"])

        print(f"\n\nDetails for cluster {cluster['name']}:\n")  # Assuming cluster has a 'name' key

        # Loop through each namespace in the cluster
        for NameSpace in cluster["namespaces"]:
            # Print deployments with no HPA for the current namespace in the cluster
            getDeploymentsWithNoHpa(NameSpace)
