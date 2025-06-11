from typing import Dict, Set

ALLOWED_QUERY_PARAMS = {
    "list_applications": {
        "name",
        "refresh",
        "project",
        "projects",
        "resource_version",
        "selector",
        "repo",
        "appNamespace",
    },
    "get_application": {
        "refresh",
        "project",
        "projects",
        "resource_version",
        "selector",
        "repo",
        "appNamespace",
    },
    "get_manifests": {
        "revision",
        "project",
        "appNamespace",
        "revisions",
        "sourcePositions",
    },
    "update_application": {"validate", "project"},
    "patch_resource": {
        "namespace",
        "resourceName",
        "version",
        "group",
        "kind",
        "patchType",
        "appNamespace",
        "project",
    },
}

ALLOWED_SYNC_FIELDS = {
    "appNamespace",
    "dryRun",
    "infos",
    "manifests",
    "name",
    "project",
    "prune",
    "resources",
    "retryStrategy",
    "revision",
    "revisions",
    "sourcePositions",
    "strategy",
    "syncOptions",
}


def validate_query_params(query: Dict, context: str) -> None:
    allowed = ALLOWED_QUERY_PARAMS.get(context)
    if allowed is None:
        raise ValueError(f"Unknown context for validation: {context}")

    for key in query:
        if key not in allowed:
            raise ValueError(f"Unsupported query parameter '{key}' for '{context}'")


def validate_sync_body(sync_body: dict):
    for key in sync_body:
        if key not in ALLOWED_SYNC_FIELDS:
            raise ValueError(f"Unsupported sync field: '{key}'")
