import configparser
import json
from urllib.parse import urljoin

import pandas as pd
import requests
# Set display options for clearer output
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', 500)
from ElasticCluster.config import tenant_api_base_url

# Load the configuration file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Read the configuration parameters
url = config.get('QA', 'url')
cert_file_path = config.get('QA', 'cert_file_path')
key_file_path = config.get('QA', 'key_file_path')
api_key = config.get('QA', 'apikey')

# Fetch the time range from config.ini
start_time = config.get('TimeRange', 'start_time')
end_time = config.get('TimeRange', 'end_time')
serviceName  = config.get('QueryParams','serviceName')
objectName  = config.get('QueryParams','objectName')

# Read the payload from the JSON file for the second request
with open('QA/Resources/DSLSearchRequestsPerTenant.json', 'r') as file:
    payload = file.read()
    # Replace the placeholders with actual values
    payload = payload.replace("{{start_time}}", start_time).replace("{{end_time}}", end_time).replace("{{serviceName}}", serviceName).replace("{{objectName}}",objectName)
    payload = json.loads(payload)

request_payload = json.dumps(payload)

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

# Send the request
try:
    kibana_response = requests.post(full_url, headers=headers, data=request_payload, cert=(cert_file_path, key_file_path))
    kibana_response.raise_for_status()
except requests.exceptions.RequestException as e:
    print("Error making the request:", e)
    kibana_response = None

# Fetch all tenants
TMS_response = requests.get(tenant_api_base_url, headers={'accept': 'application/json'})

if TMS_response.status_code == 200:
    all_tenants_data_TMS = TMS_response.json().get('value', [])
    all_tenants_TMS_df = pd.DataFrame(all_tenants_data_TMS)
else:
    print("Error fetching tenants:", TMS_response.status_code)
    print(TMS_response.text)

if kibana_response and kibana_response.status_code == 200:
    request_payload = kibana_response.json()
    bucket_data = request_payload['aggregations']['0']['buckets']
    table_data = []

    for item in bucket_data:
        org_id = item['key']
        doc_count = item['doc_count']
        count_200 = item['2-bucket']['2-metric']['value']
        count_500 = item['3-bucket']['3-metric']['value']
        table_data.append([org_id, doc_count, count_200, count_500])

    df = pd.DataFrame(table_data, columns=['orgId', 'Doc Count', 'Count of 200s', 'Count of 500s'])
    merged_df = pd.merge(df, all_tenants_TMS_df[['tenantId', 'name']], left_on='orgId', right_on='tenantId', how='left').drop('tenantId', axis=1)

    print(merged_df)
else:
    print("Error:", kibana_response.status_code if kibana_response else "No response")
    print(kibana_response.text if kibana_response else "")
