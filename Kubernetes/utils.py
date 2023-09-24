import subprocess
def parse_memory(memory):
    if memory.endswith('Gi'):
        return float(memory.rstrip('Gi')) * 1024
    elif memory.endswith('G'):
        return float(memory.rstrip('G')) * 1024
    elif memory.endswith('Mi'):
        return float(memory.rstrip('Mi'))
    elif memory.endswith('M'):
        return float(memory.rstrip('M')) / 1024
    elif memory.endswith('Ki'):
        return float(memory.rstrip('Ki')) / (1024 ** 2)
    elif memory.endswith('K'):
        return float(memory.rstrip('K')) / (1024 ** 2)
    return float(memory)

def parse_cpu(cpu):
    if cpu.endswith('m'):
        return float(cpu.rstrip('m')) / 1000
    return float(cpu)

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if error and "No resources found" not in error.decode('utf-8'):
        raise Exception(error.decode('utf-8'))
    return output.decode('utf-8')