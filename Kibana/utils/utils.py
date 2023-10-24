import configparser
import os

def load_config():
    """Load the configuration based on the current environment from config.ini."""
    config = configparser.ConfigParser()
    script_directory = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_directory, '..', 'config', 'config.ini')
    config.read(config_path)

    # Fetch the current environment from the [ENVIRONMENT] section
    current_environment = config.get('ENVIRONMENT', 'current')

    # Fetch configurations based on the current environment
    env_config = dict(config.items(current_environment))

    # Include the current environment in the config dictionary
    env_config['current'] = current_environment
    # Merge with TimeRange configurations
    time_range_config = dict(config.items('TimeRange'))
    query_params_config = dict(config.items('QueryParams'))
    env_config.update(time_range_config)
    env_config.update(query_params_config)

    return env_config
