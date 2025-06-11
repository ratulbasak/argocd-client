from .config import API_VERSION


def _prefix(path: str, version: str = None) -> str:
    ver = version or API_VERSION
    return f"/api/{ver}{path}"


# -----------------------------
# Application Routes
# -----------------------------


def apps(version: str = None) -> str:
    return _prefix(f"/applications", version)


def app(name: str, version: str = None) -> str:
    return _prefix(f"/applications/{name}", version)


def app_sync(name: str, version: str = None) -> str:
    return _prefix(f"/applications/{name}/sync", version)


def app_manifests(name: str, version: str = None) -> str:
    return _prefix(f"/applications/{name}/manifests", version)


def app_resource_tree(name: str, version: str = None) -> str:
    return _prefix(f"/applications/{name}/resource-tree", version)


def app_patch_resource(name: str, version: str = None) -> str:
    return _prefix(f"/applications/{name}/resource", version)


# -----------------------------
# ApplicationSet Routes
# -----------------------------


def appsets(version: str = None) -> str:
    return _prefix("/applicationsets", version)


def appset_name(name: str, version: str = None) -> str:
    return _prefix(f"/applicationsets/{name}", version)


# -----------------------------
# Project Routes
# -----------------------------


def projects(version: str = None) -> str:
    return _prefix("/projects", version)


def project_name(name: str, version: str = None) -> str:
    return _prefix(f"/projects/{name}", version)
