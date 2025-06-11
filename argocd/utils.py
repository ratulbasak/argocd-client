import time
import yaml
from typing import Any, Dict, List, Tuple


def load_yaml(data):
    return yaml.safe_load(data)


def merge_lists(old_list, new_list):
    """
    Merge two lists. If all items are 'key=value', deduplicate by key.
    Otherwise, deduplicate exact duplicates.
    """
    combined = old_list + new_list

    # Check if all items are in key=value format
    if all("=" in item for item in combined):
        kv_map = {}
        for item in combined:
            k, v = item.split("=", 1)
            kv_map[k] = v  # last one wins
        return [f"{k}={v}" for k, v in kv_map.items()]
    else:
        return list(dict.fromkeys(combined))  # fallback: exact deduplication


def deep_merge(base, patch):
    for key, value in patch.items():
        if key in base:
            if isinstance(base[key], dict) and isinstance(value, dict):
                deep_merge(base[key], value)
            elif isinstance(base[key], list) and isinstance(value, list):
                base[key] = merge_lists(base[key], value)
            else:
                base[key] = value
        else:
            base[key] = value


def build_query_items(params: Dict[str, Any]) -> List[Tuple[str, str]]:
    query_items = []

    for key, value in params.items():
        if isinstance(value, list):
            for item in value:
                query_items.append((key, str(item)))
        else:
            query_items.append((key, str(value)))

    return query_items
