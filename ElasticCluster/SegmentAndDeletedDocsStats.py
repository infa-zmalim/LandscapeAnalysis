import pandas as pd
import requests
from utility_functions import convert_size_to_mb,modify_volume
import os

from config import BASE_URL

# Set display options for a clearer output

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows',50000)

# Fetching data from the API for deleted docs stats
allocation_df = pd.DataFrame(requests.get(f'{BASE_URL}/_cat/indices/?format=json&v&s=store.size:desc').json())

#from file
#allocation_df = pd.read_csv("resources/NA/indicesNA", sep="\s+")

# Replace None values with 0
allocation_df.fillna(0, inplace=True)

# Convert the columns to the appropriate data type
allocation_df["docs.count"] = allocation_df["docs.count"].astype(int)
allocation_df["docs.deleted"] = allocation_df["docs.deleted"].astype(int)

# Calculating the ratio of docs.deleted to docs.count
allocation_df["deleted_to_count_ratio"] = (allocation_df["docs.deleted"] / allocation_df["docs.count"]) * 100

# Fetch data from the URL for segments stats
segments_df = pd.DataFrame(requests.get(f'{BASE_URL}/_cat/segments?v&format=json').json())

#From file
#segments_df = pd.read_csv("resources/NA/segmentsNA", sep="\s+")

segment_counts = segments_df.groupby('index').size().reset_index(name='segments_count')

# Load the CSV data
csv_path = "resources/tenantsVolumeAndUserName.csv"
csv_df = pd.read_csv(csv_path)

csv_df['volume'] = csv_df['volume'].apply(modify_volume)
# Merge the segment counts with the original segment data
merged_segments_df = pd.merge(segments_df, segment_counts, on="index", how="left")
merged_segments_df2= pd.merge(merged_segments_df,csv_df,on="index", how="left")
# Merge the dataframes on the 'index' column
final_df = pd.merge(allocation_df, merged_segments_df2, on="index", how="outer")

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
print(final_df)
# Save the result to CSV

#final_df.to_csv('../resources/CombinedStats_NA.csv', index=False)



