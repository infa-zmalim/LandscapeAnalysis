import re

def convert_to_lowercase(df, column_name):
    df[column_name] = df[column_name].str.lower()

def convert_size_to_mb(size):
    size_str = str(size)  # Convert the size to a string regardless of its original type

    if 'kb' in size_str:
        return round(float(size_str.replace('kb', '')) / 1024, 2)
    elif 'mb' in size_str:
        return round(float(size_str.replace('mb', '')), 2)
    elif 'gb' in size_str:
        return round(float(size_str.replace('gb', '')) * 1024, 2)
    elif 'b' in size_str:
        return round(float(size_str.replace('b', '')) / (1024 * 1024), 2)
    else:
        try:
            return round(float(size_str), 2)  # If no units are specified, assume it's already in MB
        except ValueError:
            return 0  # Or handle this case differently if needed


# Modify volume column
def modify_volume(value):
    # Check if the input is a string
    if isinstance(value, str):
        # Remove commas from the string
        cleaned_value = value.replace(',', '')

        # Attempt to convert the string to an integer
        try:
            value = int(cleaned_value)
        except ValueError:
            # If conversion fails, return the original value as it might not be convertible
            return value

    if value >= 1_000_000_000:   # Billion
        return str(value // 1_000_000_000) + 'B'
    elif value >= 1_000_000:     # Million
        return str(value // 1_000_000) + 'M'
    elif value >= 1_000:        # Thousand
        return str(value // 1_000) + 'k'
    return str(value)

# Extract TenantId from index
def extract_tenant_id(index_value):
    # Extract pattern based on your given example
    parts = index_value.split('-')
    if len(parts) > 1:
        return parts[1]
    return None

# Use regex to extract OrgId
def extract_org_id(index_name):
    match = re.search(r'devprod-(.*?)-', index_name)
    return match.group(1) if match else None