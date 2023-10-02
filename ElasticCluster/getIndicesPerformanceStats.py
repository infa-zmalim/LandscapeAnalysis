import pandas as pd
import requests
from Kibana.getTenantAssetData import get_tenant_asset_data
from utility_functions import modify_volume, extract_tenant_id
from config import BASE_URL

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows',50)

def getIndicesPerformanceStats():
    # Fetching data from the API for indices stats
    indices_response = requests.get(f'{BASE_URL}/_cat/indices?h=index,docs.count,store.size,refresh.time,search.query_total,search.query_time,search.query_current&format=json')
    indices_response.raise_for_status()  # Check if request was successful
    indices_data = indices_response.json()
    indices_df = pd.DataFrame(indices_data)
    # print(f"Indices:", indices_df)
    # print(f"Indices:\n{indices_df.to_string()}")
    indices_df['index'] = indices_df['index'].apply(extract_tenant_id)
    telemetry_df = get_tenant_asset_data()
    merged_df = pd.merge(indices_df, telemetry_df, left_on='index', right_on='Org', how='left')
    merged_df['search.query_total'] = pd.to_numeric(merged_df['search.query_total'])
    merged_df = merged_df.sort_values(by='search.query_total', ascending=False)
    merged_df['search.query_total'] = merged_df['search.query_total'].apply(modify_volume)

    return merged_df

if __name__ == "__main__":
    getIndicesPerformanceStats=getIndicesPerformanceStats()
    print(getIndicesPerformanceStats)
