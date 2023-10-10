import json
import os
from urllib.parse import urljoin
import pandas as pd
import requests
from ElasticCluster.config import tenant_api_base_url

# Importing required functions and modules
from Kibana.utils.utils import load_config
from Kibana.getTenantAssetData import get_tenant_asset_data

def get_kibana_service_data():
    configurations = load_config()  # Using the new load_config function

    # Set display options for clearer output
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_rows', 50)

    # Load configurations
    url = configurations['url']
    cert_file_path = configurations['cert_file_path']
    key_file_path = configurations['key_file_path']
    api_key = configurations['apikey']
    start_time = configurations.get('start_time', '')
    end_time = configurations.get('end_time', '')
    serviceName = configurations.get('servicename', '')
    objectName = configurations.get('objectname', '')
    path = configurations.get('path', '')


    # Fetch the JSON payload
    script_directory = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(script_directory, 'Resources', 'DSLSearchRequestsPerTenant.json')
    with open(json_file_path, 'r') as file:
        payload = file.read().replace("{{start_time}}", start_time).replace("{{end_time}}", end_time)
        payload = payload.replace("{{serviceName}}", serviceName).replace("{{objectName}}", objectName)
        payload = json.loads(payload)

    request_payload = json.dumps(payload)
    full_url = urljoin(url, path)

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    # print(json.dumps(request_payload, indent=4))
    # Send the request
    try:
        kibana_response = requests.post(full_url, headers=headers, data=request_payload, cert=(cert_file_path, key_file_path))
        kibana_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error making the request:", e)
        kibana_response = None

    # Fetch all tenants
    TMS_response = requests.get(tenant_api_base_url, headers={'accept': 'application/json'})
    if TMS_response.status_code != 200:
        print("Error fetching tenants:", TMS_response.status_code)
        print(TMS_response.text)

    all_tenants_data_TMS = TMS_response.json().get('value', [])
    all_tenants_TMS_df = pd.DataFrame(all_tenants_data_TMS)
    all_tenants_TMS_df['tenantId'] = all_tenants_TMS_df['tenantId'].str.lower()

    merged_df = None
    if kibana_response and kibana_response.status_code == 200:
        response_payload = kibana_response.json()
        bucket_data = response_payload.get('aggregations', {}).get('0', {}).get('buckets', [])
        table_data = []

        for item in bucket_data:
            org_id = item['key']
            doc_count = item['doc_count']
            count_200 = item['2-bucket']['2-metric']['value']
            count_500 = item['3-bucket']['3-metric']['value']
            table_data.append([org_id, doc_count, count_200, count_500])

        df = pd.DataFrame(table_data, columns=['orgId', f'{serviceName} {objectName} requests', 'Count of 200s', 'Count of 500s'])
        df['orgId'] = df['orgId'].str.lower()
        merged_df = pd.merge(df, all_tenants_TMS_df[['tenantId', 'name']], left_on='orgId', right_on='tenantId', how='left').drop('tenantId', axis=1)

        # Fetch tenant asset data
        tenant_asset_df = get_tenant_asset_data(configurations)
        final_df = pd.merge(merged_df, tenant_asset_df, left_on='orgId', right_on='Org', how='left')
    else:
        print(f"Failed to fetch data from Kibana. Status Code: {kibana_response.status_code if kibana_response else 'No Response'}")
        final_df = None  # Or you can return an empty DataFrame or any other suitable default value

    return final_df

if __name__ == "__main__":
    df = get_kibana_service_data()
    print(df)
