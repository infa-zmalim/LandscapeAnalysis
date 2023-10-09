from Kubernetes.utils.utils import run_command, clusters
import pandas as pd
# Set display options for clearer output
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', None)
import re

def get_hpa(namespace):
    cmd_output = run_command(f"kubectl get hpa -n {namespace}")
    lines = cmd_output.split('\n') if cmd_output else []

    if not lines:
        return []

    headers = re.split(r'\s{2,}', lines[0])  # Split headers on 2 or more spaces

    hpa_data = []
    for line in lines[1:]:
        if line:
            values = re.split(r'\s{2,}', line)
            hpa_dict = dict(zip(headers, values))
            hpa_data.append(hpa_dict)

    return hpa_data

def getHPAStatsForCluster(cluster):
    # Update kubeconfig for the cluster
    run_command(cluster["config"])

    cluster_hpa_data = []
    # Fetch HPA details for each namespace in the cluster
    for namespace in cluster["namespaces"]:
        hpa_data = get_hpa(namespace)
        cluster_hpa_data.extend(hpa_data)

    # Convert list of dictionaries to a DataFrame for this cluster
    df = pd.DataFrame(cluster_hpa_data)
    return df.sort_values(by='REPLICAS', ascending=False)

if __name__ == "__main__":
    for cluster in clusters:
        print(f"\n\nHPA details for cluster {cluster['name']}:\n")  # Assuming cluster has a 'name' key
        df_hpa_stats = getHPAStatsForCluster(cluster)
        print(df_hpa_stats)
