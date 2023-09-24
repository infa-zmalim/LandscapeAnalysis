def parse_memory(memory):
    if memory.endswith('Gi'):
        return float(memory.rstrip('Gi')) * 1024
    elif memory.endswith('Mi'):
        return float(memory.rstrip('Mi'))
    elif memory.endswith('M'):
        return float(memory.rstrip('M')) / 1024
    elif memory.endswith('Ki'):
        return float(memory.rstrip('Ki')) / (1024 ** 2)
    return float(memory)
