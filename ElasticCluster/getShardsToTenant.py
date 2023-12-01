import pandas as pd
import requests
from Kibana.getTenantAssetData import get_tenant_asset_data
from Kibana.utils.utils import load_config
from utility_functions import extract_tenant_id
from config import BASE_URL

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows',50)

def getShardsToTenants(configurations):
    csv_df = pd.read_csv('./resources/DEVPROD/tenantUserNamesPwd.csv')
    valid_values = csv_df['Username'].unique()
    telemetry_df = get_tenant_asset_data(configurations)
    # telemetry_df = telemetry_df[telemetry_df['Tenant'].isin(valid_values)]
    shards_response = requests.get(f'{BASE_URL}/_cat/shards?h=index,node&format=json')
    shards_response.raise_for_status()  # Check if request was successful
    shards_data = shards_response.json()
    shards_df = pd.DataFrame(shards_data)
    # print(shards_df)
    shards_df['Extracted_index'] = shards_df['index'].apply(extract_tenant_id)
    merged_df = pd.merge(shards_df, telemetry_df, left_on='Extracted_index', right_on='Org', how='left')
    merged_df = merged_df[merged_df['Tenant'].isin(valid_values)]
    node_index_counts = merged_df.groupby('node').size()
    node_index_counts_df = node_index_counts.reset_index(name='index_count')
    print(node_index_counts_df)

if __name__ == "__main__":
    configurations = load_config()
    getShardsToTenants = getShardsToTenants(configurations)
    # print(getShardsToTenants)
