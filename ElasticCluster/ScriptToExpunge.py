import pandas as pd
import requests
import time

from ElasticCluster.config import BASE_URL

#URL for search Cluster
#base_url = 'https://vpc-ccgf-qa-devprod-cdgc-v2-es-v4za6cpj3x2r4gtmgtsv2a2o3u.us-west-2.es.amazonaws.com'
#URL for Audit
base_url = f'{BASE_URL}'


indices_endpoint = '/_cat/indices/?format=json&v&s=store.size:desc'
forcemerge_endpoint = '/_forcemerge?only_expunge_deletes=true'

# Fetching the data from the API
response = requests.get(base_url + indices_endpoint)
data = response.json()

# Convert to DataFrame
df = pd.DataFrame(data)
df.fillna(0, inplace=True)
df["docs.count"] = df["docs.count"].astype(int)
df["docs.deleted"] = df["docs.deleted"].astype(int)

# Calculate ratio
df["deleted_to_count_ratio"] = (df["docs.deleted"] / df["docs.count"]) * 100
df['size_in_gb'] = df['store.size'].str.extract(r'(\d+\.?\d*)')[0].astype(float)
size_unit = df['store.size'].str[-2:].str.lower()

df.loc[size_unit == 'kb', 'size_in_gb'] /= 1e6
df.loc[size_unit == 'mb', 'size_in_gb'] /= 1e3
df.loc[size_unit == 'b', 'size_in_gb'] /= 1e9
df.loc[df['store.size'] == '0', 'size_in_gb'] = 0.0

#filtered_indices = df[(df["deleted_to_count_ratio"] > 1) & (df["size_in_gb"] < 100) ]['index'].tolist()
#filtered_indices = df[(df["deleted_to_count_ratio"] > 0) & (df["size_in_gb"] < 100) ]['index'].tolist()
filtered_indices = df[
    (df["deleted_to_count_ratio"] > 0) &
    ~df['index'].isin([
        'devprod-9ibyw4vm3etgvfclpfcsob-mkg_document_store-ccgf-contentv2',
        'devprod-4kkblzb73mzg0zbb6jorms-mkg_document_store-ccgf-contentv2'
    ])
    ]['index'].tolist()
failed_indices = []

for index_name in filtered_indices:
    try:
        response = requests.post(base_url + '/' + index_name + forcemerge_endpoint, timeout=502500)  # extended timeout
        if response.status_code == 200:
            print(f"Successfully force expunged {index_name}")
        else:
            print(f"Failed to expunge {index_name}. Status code: {response.status_code}, Response: {response.text}")
            failed_indices.append(index_name)
    except requests.exceptions.Timeout:
        print(f"Timeout occurred while expunging {index_name}.")
        failed_indices.append(index_name)

    #time.sleep(30)  # increased sleep duration

print("\nFailed to expunge the following indices due to timeouts or errors:")
for index in failed_indices:
    print(index)

print("\nIndices with a deleted_to_count_ratio > 20%:")
print(df[df["deleted_to_count_ratio"] > 20]['index'])
