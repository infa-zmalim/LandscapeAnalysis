import pandas as pd
import requests
from utility_functions import convert_size_to_mb, modify_volume, extract_tenant_id, convert_to_lowercase
import os

from config import BASE_URL

# Set display options for a clearer output

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', 1000)

# Fetching data from the API for deleted docs stats
indices_df = pd.DataFrame(requests.get(f'{BASE_URL}/_cat/indices/?format=json&v&s=store.size:desc').json())

#from file
#allocation_df = pd.read_csv("resources/NA/indicesAuditNA", sep="\s+")

# Replace None values with 0
indices_df.fillna(0, inplace=True)

# Convert the columns to the appropriate data type
indices_df["docs.count"] = indices_df["docs.count"].astype(int)
indices_df["docs.deleted"] = indices_df["docs.deleted"].astype(int)

# Calculating the ratio of docs.deleted to docs.count
indices_df["deleted_to_count_ratio"] = round((indices_df["docs.deleted"] / indices_df["docs.count"]) * 100 , 2)

# Fetch data from the URL for segments stats
segments_df = pd.DataFrame(requests.get(f'{BASE_URL}/_cat/segments?v&format=json').json())

#From file
#segments_df = pd.read_csv("resources/NA/segmentsAuditNA", sep="\s+")

segment_counts = segments_df.groupby('index').size().reset_index(name='segments_count')

# Load the CSV data
csv_path = "resources/DEVPROD/telemetryDEVPROD.csv"
telemetry_df = pd.read_csv(csv_path, sep="\s+")

telemetry_df['Total'] = telemetry_df['Total'].apply(modify_volume)
convert_to_lowercase(telemetry_df, 'TenantId')

# Merge the segment counts with the original segment data
merged_segments_df = pd.merge(segments_df, segment_counts, on="index", how="left")

# Apply the function to extract TenantId
merged_segments_df['TenantId_extracted'] = merged_segments_df['index'].apply(extract_tenant_id)

# Now, merge using the extracted TenantId
merged_segments_df2 = pd.merge(merged_segments_df, telemetry_df, left_on="TenantId_extracted", right_on="TenantId", how="left")

# Optionally, you can drop the 'TenantId_extracted' column if not required
merged_segments_df2.drop(columns=['TenantId_extracted'], inplace=True)

# Merge the dataframes on the 'index' column
final_df = pd.merge(indices_df, merged_segments_df2, on="index", how="outer")


final_df['store.size'] = final_df['store.size'].apply(convert_size_to_mb)
final_df['pri.store.size'] = final_df['pri.store.size'].apply(convert_size_to_mb)
final_df['size'] = final_df['size'].apply(convert_size_to_mb)

# Convert 'size' column to numeric
final_df['size'] = pd.to_numeric(final_df['size'], errors='coerce')


# Calculate the required statistics for the 'size' column for each index
final_df['mean_size'] = final_df.groupby('index')['size'].transform('mean')
final_df['variance_size'] = final_df.groupby('index')['size'].transform('var')
final_df['95th_percentile_size'] = final_df.groupby('index')['size'].transform(lambda x: x.quantile(0.95))
final_df['std_dev_size(mb)'] = final_df.groupby('index')['size'].transform('std')


# Print the result
#print(final_df)

# Drop duplicates based on the 'index' column and keep the first occurrence
unique_df = final_df.drop_duplicates(subset='index', keep='first')

# Print the filtered result
print(unique_df)


unique_df.to_csv('resources/CombinedStats_DEVPROD.csv', index=False)



