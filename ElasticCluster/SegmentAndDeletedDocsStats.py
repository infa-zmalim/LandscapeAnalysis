import pandas as pd
import requests

from config import BASE_URL, tenant_api_base_url
from utility_functions import convert_size_to_mb, modify_volume, extract_tenant_id

# Set display options for clearer output
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', 500)

# Fetching data from the API for deleted docs stats
indices_df = pd.DataFrame(requests.get(f'{BASE_URL}/_cat/indices/?format=json&v&s=store.size:desc').json())
# from file
# indices_df = pd.read_csv("resources/NA/indicesNA", sep="\s+")

# Replace None values with 0 and convert columns to appropriate data types
indices_df.fillna(0, inplace=True)
indices_df["docs.count"] = indices_df["docs.count"].astype(int)
indices_df["docs.deleted"] = indices_df["docs.deleted"].astype(int)
indices_df["deleted_to_count_ratio"] = round((indices_df["docs.deleted"] / indices_df["docs.count"]) * 100, 2)
indices_df['store.size'] = indices_df['store.size'].apply(convert_size_to_mb)
indices_df['pri.store.size'] = indices_df['pri.store.size'].apply(convert_size_to_mb)

# Fetch data from the URL for segments stats
segments_df = pd.DataFrame(requests.get(f'{BASE_URL}/_cat/segments?v&format=json').json())
# From file
# segments_df = pd.read_csv("resources/NA/segmentsNA", sep="\s+",low_memory=False)

segments_df['size'] = pd.to_numeric(segments_df['size'].apply(convert_size_to_mb), errors='coerce')
segments_df['mean_size'] = segments_df.groupby('index')['size'].transform('mean').round(2)
segments_df['95th_percentile_size'] = segments_df.groupby('index')['size'].transform(lambda x: x.quantile(0.95)).round(
    2)
segments_df['std_dev_size(mb)'] = segments_df.groupby('index')['size'].transform('std').round(2)
segment_counts = segments_df.groupby('index').size().reset_index(name='segments_count')
# Merge the segments df with the segments count dataframes
merged_segments_df = pd.merge(segments_df, segment_counts, on="index", how="left")
merged_segments_unique_df = merged_segments_df.drop_duplicates(subset='index', keep='first')

# merge the indices with the segmentsdf
merged_indices_segments_unique_df = pd.merge(indices_df, merged_segments_unique_df, on="index", how="left")

merged_indices_segments_unique_df['TenantId_extracted'] = merged_indices_segments_unique_df['index'].apply(
    extract_tenant_id)

# Load the CSV data
csv_path = "resources/DEVPROD/telemetryDEVPROD.csv"
telemetry_df = pd.read_csv(csv_path, sep="\s+")
telemetry_df['Total'] = telemetry_df['Total'].apply(modify_volume)
telemetry_df['Telemetry_TenantId_lowercase'] = telemetry_df['TenantId'].str.lower()

merged_indices_segments_telemetry_unique_df = pd.merge(merged_indices_segments_unique_df, telemetry_df,
                                                       left_on='TenantId_extracted',
                                                       right_on='Telemetry_TenantId_lowercase', how='left')

# Fetch all tenants
TMS_response = requests.get(tenant_api_base_url, headers={'accept': 'application/json'})
if TMS_response.status_code == 200:
    all_tenants_data_TMS = TMS_response.json().get('value', [])
    all_tenants_TMS_df = pd.DataFrame(all_tenants_data_TMS)
    all_tenants_TMS_df['TMS_TenantId_lowercase'] = all_tenants_TMS_df['tenantId'].str.lower()
    final_df = pd.merge(merged_indices_segments_telemetry_unique_df, all_tenants_TMS_df, left_on='TenantId_extracted',
                        right_on='TMS_TenantId_lowercase', how='left')
    # Find tenants that are in all_tenants_df but not in unique_df
    missing_tenants_df = all_tenants_TMS_df[
        ~all_tenants_TMS_df['TMS_TenantId_lowercase'].isin(merged_indices_segments_telemetry_unique_df['TenantId'])]
    # If you want to print or store them
    # final_df.drop(columns=['tenantId', 'TMS_TenantId_lowercase', 'TMS_TenantId_lowercase', 'Telemetry_TenantId_lowercase'],inplace=True)

    # Print the filtered result
# print(final_df[final_df['index'] == 'devprod-9ibyw4vm3etgvfclpfcsob-mkg_document_store-ccgf-contentv2'])
print(final_df[['index', 'segments_count', 'Tenant']])
# print(final_df)

# Output to a CSV
# final_df.to_csv('Output/CombinedStats_AUDIT_DEVPROD.csv', index=False)
# missing_tenants_df.to_csv('Output/MissingTenantsFromIndexButInTMS_AUDIT_DEVPROD.csv', index=False)
