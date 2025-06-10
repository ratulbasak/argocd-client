from typing import Dict, Set

ALLOWED_QUERY_PARAMS = {
    "list_applications": {
        "name", "refresh", "project", "projects", "resource_version", "selector", "repo", "appNamespace"
    },
    "get_application": {
        "refresh", "project", "projects", "resource_version", "selector", "repo", "appNamespace"
    },
    "get_manifests": {
        "revision", "project", "appNamespace", "revisions", "sourcePositions"
    }, 
    "update_application": {"validate", "project"}
}

def validate_query_params(query: Dict, context: str) -> None:
    allowed = ALLOWED_QUERY_PARAMS.get(context)
    if allowed is None:
        raise ValueError(f"Unknown context for validation: {context}")

    for key in query:
        if key not in allowed:
            raise ValueError(f"Unsupported query parameter '{key}' for '{context}'")
