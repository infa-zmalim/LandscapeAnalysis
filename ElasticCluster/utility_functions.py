def convert_size_to_mb(size):
    size_str = str(size)  # Convert the size to a string regardless of its original type

    if 'kb' in size_str:
        return float(size_str.replace('kb', '')) / 1024
    elif 'mb' in size_str:
        return float(size_str.replace('mb', ''))
    elif 'gb' in size_str:
        return float(size_str.replace('gb', '')) * 1024
    elif 'b' in size_str:
        return float(size_str.replace('b', '')) / (1024 * 1024)
    else:
        try:
            return float(size_str)  # If no units are specified, assume it's already in MB
        except ValueError:
            return 0  # Or handle this case differently if needed

# Modify volume column
def modify_volume(value):
    if value >= 1_000_000_000:   # Billion
        return str(value // 1_000_000_000) + 'B'
    elif value >= 1_000_000:     # Million
        return str(value // 1_000_000) + 'M'
    elif value >= 1_000:        # Thousand
        return str(value // 1_000) + 'k'
    return str(value)


