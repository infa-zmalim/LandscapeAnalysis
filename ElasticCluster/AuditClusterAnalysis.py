import pandas as pd
from utility_functions import convert_size_to_mb, convert_to_lowercase

# Define the paths to the files
audit_cluster = "resources/DEVPROD/DEVProdIndex"
asset_Cluster = "resources/DEVPROD//DEVPRODAudit"
telemetry_csv = "resources/DEVPROD//telemetry.csv"  # Replace with the actual CSV file path
# Set the display options
pd.set_option('display.width', 5000)
# Set the display options for pandas
pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.width', None)  # Set the display width to max
pd.set_option('display.max_colwidth', None)  # Show full content of each column

pd.set_option('display.max_rows', 500)  # Set max_rows to None to display all rows
# Converting the data to a pandas DataFrame

# Define the column names for the first file
column_names_audit = [
    "health_audit", "status_audit", "index_audit", "uuid_audit", "pri_audit", "rep_audit",
    "docs.count_audit", "docs.deleted_audit", "store.size_audit", "pri.store.size_audit"
]

# Define the column names for the second file
column_names_Asset = [
    "health_searchES", "status_searchES", "index_searchES", "uuid_searchES", "pri_searchES", "rep_searchES",
    "docs.count_searchES", "docs.deleted_searchES", "store.size_searchES", "pri.store.size_searchES"
]

# Read the first file into a DataFrame
df_audit_cluster = pd.read_csv(audit_cluster, sep="\s+", header=None, names=column_names_audit, skiprows=1)

# Read the second file into another DataFrame
df_asset_Cluster = pd.read_csv(asset_Cluster, sep="\s+", header=None, names=column_names_Asset, skiprows=1)

# Read the CSV file into another DataFrame
df_telemetry_csv = pd.read_csv(telemetry_csv)  # Assumes first row is header

convert_to_lowercase(df_telemetry_csv, 'TenantId')
#print(df_telemetry_csv)
# Extract the subset of the index value from df_audit_cluster
df_audit_cluster['subset_index_audit'] = df_audit_cluster['index_audit'].str.split('-', expand=True)[1]
#print(df_audit_cluster)
# Extract the subset of the index value from df_asset_Cluster
df_asset_Cluster['subset_index_searchES'] = df_asset_Cluster['index_searchES'].str.split('-', expand=True)[1]
#print(df_asset_Cluster)
# Perform inner join between df_audit_cluster and df_asset_Cluster based on subset_index
merged_df = df_audit_cluster.merge(df_asset_Cluster, left_on='subset_index_audit', right_on='subset_index_searchES')
#print(merged_df)
# Perform inner join between merged_df and df_telemetry_csv based on subset_index and TenantId
final_merged_df = merged_df.merge(df_telemetry_csv, left_on='subset_index_audit', right_on='TenantId')
#print(final_merged_df)
# Define a function to convert sizes to MB

# Convert store.size and pri.store.size columns to MB in final_merged_df
final_merged_df['store.size_audit'] = final_merged_df['store.size_audit'].apply(convert_size_to_mb)
final_merged_df['pri.store.size_audit'] = final_merged_df['pri.store.size_audit'].apply(convert_size_to_mb)
final_merged_df['store.size_searchES'] = final_merged_df['store.size_searchES'].apply(convert_size_to_mb)
final_merged_df['pri.store.size_searchES'] = final_merged_df['pri.store.size_searchES'].apply(convert_size_to_mb)
final_merged_df.drop_duplicates(subset=['index_audit'], keep='first', inplace=True)
# Sort the DataFrame on pri.store.size_audit (descending) and TenantId (ascending)
final_merged_df.sort_values(by=['pri.store.size_audit', 'TenantId'], ascending=[False, True], inplace=True)


# Save the final merged DataFrame to a CSV file
output_folder = "venv/resources/DEVPROD/output/"  # Specify the output folder
#final_merged_df.to_csv(output_folder + "final_merged_df.csv", index=False)
print(final_merged_df)

# Reset the display options to their default values
pd.reset_option("display.max_columns")
