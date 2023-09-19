import pandas as pd
import requests
from config import BASE_URL

# Fetching the data from the API
response = requests.get(f'{BASE_URL}/_cat/indices/?format=json&v&s=store.size:desc')
data = response.json()
# Set display options for a clearer output
pd.set_option('display.width', 5000)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', 10000)
# Converting the data to a pandas DataFrame
df = pd.DataFrame(data)

# Replace None values with 0
df.fillna(0, inplace=True)

# Convert the columns to the appropriate data type
df["docs.count"] = df["docs.count"].astype(int)
df["docs.deleted"] = df["docs.deleted"].astype(int)

# Calculating the ratio of docs.deleted to docs.count
df["deleted_to_count_ratio"] = (df["docs.deleted"] / df["docs.count"])*100

df_sorted = df.sort_values(by="docs.deleted", ascending=False)

# Output all the columns
print(df_sorted)