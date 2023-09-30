import configparser
import requests
import json
from urllib.parse import urljoin
import plotly.graph_objects as go  # <-- Import Plotly
import os

# Load the configuration file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Read the configuration parameters
url = config.get('QA', 'url')
cert_file_path = config.get('QA', 'cert_file_path')
key_file_path = config.get('QA', 'key_file_path')
api_key = config.get('QA', 'apikey')

# Read the payload from the JSON file
with open('QA/Resources/DSLClusterCount.json', 'r') as file:
    payload = json.load(file)

data = json.dumps(payload)

# Define the path
path = "fluentbit-*-ccgf-*/_search"

# Join the base URL with the path
full_url = urljoin(url, path)
print("Full URL:", full_url)

# Headers
headers = {
    "Content-Type": "application/json",
    "x-api-key": api_key
}
print("Headers:", headers)

print("Payload:", data)

# Initialize response as None
response = None

try:
    response = requests.post(full_url, headers=headers, data=data, cert=(cert_file_path, key_file_path))
except requests.exceptions.RequestException as e:
    print("Error making the request:", e)

# Check the response
if response is not None and response.status_code == 200:
    print("Success!")
    data = json.loads(response.text)

    # Check if 'aggregations' key exists in the response
    if 'aggregations' not in data:
        print("No aggregations in the response. Please check the Elasticsearch query and index.")
        print("Response:", json.dumps(data, indent=4))
    else:
        # Extract the bucket information from the aggregation result
        buckets = data["aggregations"]["clusters"]["buckets"]

        # Prepare data for plotting
        cluster_names = [bucket['key'] for bucket in buckets]
        record_counts = [bucket['doc_count'] for bucket in buckets]

        # Create an interactive donut plot using Plotly
        fig = go.Figure(data=[go.Pie(labels=cluster_names, values=record_counts, hole=.4)])
        fig.update_layout(title_text='Distribution of Records for each Cluster (Last Hour)')
        fig.show()

else:
    print("Failed to retrieve data.")
    if response is not None:
        print("Status Code:", response.status_code)
        print(response.text)