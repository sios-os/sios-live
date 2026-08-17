import json

def load_config(json_str):
    """Parse JSON string and return a dictionary."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

def get_value(config, key, default=None):
    """Safely get a nested value using dot notation (e.g. 'a.b.c')."""
    keys = key.split('.')
    for k in keys:
        if isinstance(config, dict) and k in config:
            config = config[k]
        else:
            return default
    return config

def merge_configs(base, override):
    """Deep-merge two dictionaries."""
    result = base.copy()
    for k, v in override.items():
        if isinstance(v, dict) and k in result and isinstance(result[k], dict):
            result[k] = merge_configs(result[k], v)
        else:
            result[k] = v
    return result