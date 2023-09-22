import pandas as pd
import requests
from utility_functions import convert_size_to_mb, modify_volume, extract_tenant_id, convert_to_lowercase
import os
from config import BASE_URL, NA_API_BASE_URL, DEVPROD_API_BASE_URL, tenant_api_base_url

# Set display options for clearer output
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', None)

# Fetching data from the API for deleted docs stats
# indices_df = pd.DataFrame(requests.get(f'{BASE_URL}/_cat/indices/?format=json&v&s=store.size:desc').json())
#from file
indices_df = pd.read_csv("resources/NA/indicesNA", sep="\s+")

# Replace None values with 0 and convert columns to appropriate data types
indices_df.fillna(0, inplace=True)
indices_df["docs.count"] = indices_df["docs.count"].astype(int)
indices_df["docs.deleted"] = indices_df["docs.deleted"].astype(int)
indices_df["deleted_to_count_ratio"] = round((indices_df["docs.deleted"] / indices_df["docs.count"]) * 100, 2)

# Fetch data from the URL for segments stats
#segments_df = pd.DataFrame(requests.get(f'{BASE_URL}/_cat/segments?v&format=json').json())
#From file
segments_df = pd.read_csv("resources/NA/segmentsNA", sep="\s+",low_memory=False)
segment_counts = segments_df.groupby('index').size().reset_index(name='segments_count')

# Load the CSV data
csv_path = "resources/NA/telemetryNA.csv"
telemetry_df = pd.read_csv(csv_path, sep="\s+")
telemetry_df['Total'] = telemetry_df['Total'].apply(modify_volume)
telemetry_df['TenantId_lowercase'] = telemetry_df['TenantId'].str.lower()

# Merge the dataframes
merged_segments_df = pd.merge(segments_df, segment_counts, on="index", how="left")
merged_segments_df['TenantId_extracted'] = merged_segments_df['index'].apply(extract_tenant_id)
merged_segments_df2 = pd.merge(merged_segments_df, telemetry_df, left_on="TenantId_extracted", right_on="TenantId_lowercase", how="left")
merged_segments_df2.drop(columns=['TenantId_extracted', 'TenantId_lowercase'], inplace=True)
final_df = pd.merge(indices_df, merged_segments_df2, on="index", how="outer")

# Apply conversion functions and calculate statistics
final_df['store.size'] = final_df['store.size'].apply(convert_size_to_mb)
final_df['pri.store.size'] = final_df['pri.store.size'].apply(convert_size_to_mb)
final_df['size'] = pd.to_numeric(final_df['size'].apply(convert_size_to_mb), errors='coerce')
final_df['mean_size'] = final_df.groupby('index')['size'].transform('mean').round(2)
final_df['95th_percentile_size'] = final_df.groupby('index')['size'].transform(lambda x: x.quantile(0.95)).round(2)
final_df['std_dev_size(mb)'] = final_df.groupby('index')['size'].transform('std').round(2)
unique_df = final_df.drop_duplicates(subset='index', keep='first')

# Fetch all tenants
response = requests.get(tenant_api_base_url, headers={'accept': 'application/json'})
if response.status_code == 200:
    all_tenants_data = response.json().get('value', [])
    all_tenants_df = pd.DataFrame(all_tenants_data)
    final_df = pd.merge(unique_df, all_tenants_df, left_on='TenantId', right_on='tenantId', how='left')
    # Find tenants that are in all_tenants_df but not in unique_df
    missing_tenants_df = all_tenants_df[~all_tenants_df['tenantId'].isin(unique_df['TenantId'])]
    # If you want to print or store them
    final_df.drop(columns=['tenantId'], inplace=True)

# Print the filtered result
#print(final_df)
final_df.to_csv('Output/CombinedStats_NA.csv', index=False)
missing_tenants_df.to_csv('Output/MissingTenantsFromIndex_NA.csv', index=False)
