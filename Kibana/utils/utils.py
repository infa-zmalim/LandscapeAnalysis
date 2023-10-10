import configparser
import os

def load_config():
    """Load the configuration based on the current environment from config.ini."""
    config = configparser.ConfigParser()
    script_directory = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_directory, '..', 'config', 'config.ini')  # Move one directory up and then to 'config'
    config.read(config_path)

    # Fetch the current environment from the [ENVIRONMENT] section
    current_environment = config.get('ENVIRONMENT', 'current')

    # Fetch configurations based on the current environment
    env_config = dict(config.items(current_environment))

    # Include the current environment in the config dictionary
    env_config['current'] = current_environment

    return env_config
