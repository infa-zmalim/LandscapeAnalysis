import json
import os
from urllib.parse import urljoin
import pandas as pd
import requests
from ElasticCluster.utility_functions import modify_volume
from Kibana.utils.utils import load_config


def get_tenant_asset_data(configurations):
    # Set display options for clearer output
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_rows', None)

    script_directory = os.path.dirname(os.path.abspath(__file__))

    url = configurations['url']
    cert_file_path = os.path.join(script_directory, configurations['cert_file_path'])
    key_file_path = os.path.join(script_directory, configurations['key_file_path'])
    api_key = configurations['apikey']

    json_file_path = os.path.join(script_directory, 'Resources', 'DSLTenantAssetVolumeData.json')

    with open(json_file_path, 'r') as file:
        payload = file.read()
        payload = json.loads(payload)
    request_payload = json.dumps(payload)

    path = "fluentbit-*-ccgf-*/_search"
    full_url = urljoin(url, path)

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }

    try:
        kibana_response = requests.post(full_url, headers=headers, data=request_payload, cert=(cert_file_path, key_file_path))
        kibana_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error making the request:", e)
        kibana_response = None

    df = None
    if kibana_response and kibana_response.status_code == 200:
        request_payload = kibana_response.json()
        # print(json.dumps(request_payload, indent=4))
        if 'aggregations' in request_payload and '0' in request_payload['aggregations']:
            bucket_data = request_payload['aggregations']['0']['buckets']
        else:
            print("Aggregations not found in the API response")
            return

        df_data = []
        for item in bucket_data:
            org = item['key']
            inner_buckets = item['1']['buckets']
            for inner_item in inner_buckets:
                tenant = inner_item['key']
                business_assets_sum = round(inner_item['2-bucket']['2-metric']['top'][0]['metrics']['parsed.key2.key7n'])
                technical_assets_sum = round(inner_item['3-bucket']['3-metric']['top'][0]['metrics']['parsed.key2.key8n'])
                marketplace_sum = round(inner_item['4-bucket']['4-metric']['top'][0]['metrics']['parsed.key2.key9n'])
                total_sum = round(inner_item['5-bucket']['5-metric']['top'][0]['metrics']['parsed.key2.key4n'])
                df_data.append([org, tenant, business_assets_sum, technical_assets_sum, marketplace_sum, total_sum])

        df = pd.DataFrame(df_data, columns=['Org', 'Tenant', 'Business Assets', 'Technical Assets', 'Marketplace', 'Total'])
        df = df.sort_values(by='Total', ascending=False)
        df['Org'] = df['Org'].str.lower()
        cols_to_modify = ['Business Assets', 'Technical Assets', 'Marketplace', 'Total']
        for col in cols_to_modify:
            df[col] = df[col].apply(modify_volume)
    return df

if __name__ == "__main__":
    configurations = load_config()
    df = get_tenant_asset_data(configurations)
    print(df)
