import copy
import json
from urllib.parse import urlencode
from typing import Dict

from .http import HttpClient
from .utils import build_query_items, deep_merge
from .api_routes import app, apps, app_sync, app_manifests, appsets
from .logger import get_logger
from .config import API_REQUEST_TIMEOUT
from .validators import validate_query_params


class ArgoCDClient:
    def __init__(self, api_url, token, proxies, timeout=API_REQUEST_TIMEOUT, verify_ssl=False, debug=False):
        self.api_url = api_url.rstrip("/")
        self.logger = get_logger(debug=debug)
        self.http = HttpClient(
            base_url=api_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            proxies=proxies,
            timeout=timeout,
            verify_ssl=verify_ssl,
            logger=self.logger
        )


    def list_applications(self, query_params: dict = None):
        query_params = query_params or {}
        validate_query_params(query_params, "list_applications")
        query_string = urlencode(build_query_items(query_params))
        path = apps()
        if query_string:
            path += f"?{query_string}"

        self.logger.debug(f"GET {self.api_url}{path}")

        response = self.http.get(path)
        if response.status_code != 200:
            self.logger.error(f"Failed to list applications: {response.status_code}, {response.text}")
            raise Exception({
                "success": False,
                "status": response.status_code, 
                "msg": response.json(),
                "entrypoint": "list_applications"
            })
        return response.json()


    def get_application(self, name, query_params: dict = None) -> Dict:
        query_params = query_params or {}
        validate_query_params(query_params, "get_application")
        query_string = urlencode(build_query_items(query_params))
        path = app(name)
        if query_string:
            path += f"?{query_string}"

        self.logger.debug(f"GET {self.api_url}{path}")
        response = self.http.get(path)

        self.logger.debug(f"Response {response.status_code}: {response.text}")
        if response.status_code == 200:
            return response.json()
        else:
            self.logger.error(f"Failed to get application '{name}': {response.status_code}, {response.text}")
            raise Exception({
                "success": False,
                "status": response.status_code, 
                "msg": response.json(),
                "entrypoint": "get_application"
            })


    def get_application_manifests(self, name, query_params: dict = None):
        query_params = query_params or {}
        validate_query_params(query_params, "get_manifests")
        query_string = urlencode(build_query_items(query_params))
        path = app_manifests(name)
        if query_string:
            path += f"?{query_string}"

        self.logger.info(f"Getting manifests for application '{name}'")

        response = self.http.get(path)
        self.logger.debug(f"Response {response.status_code}: {response.text}")
        if response.status_code != 200:
            self.logger.error(f"Failed to get manifests for application '{name}': {response.status_code}, {response.text}")
            raise Exception({
                "success": False,
                "status": response.status_code, 
                "msg": response.json(),
                "entrypoint": "get_application_manifests"
            })
        return response.json()


    def update_application(self, app_body: dict, query_params: dict = None) -> Dict:
        query_params = query_params or {}
        validate_query_params(query_params, "update_application")

        metadata = app_body.get("metadata", {})
        app_name = metadata.get("name")
        if not app_name:
            raise ValueError("metadata.name is required in the application body.")

        # Construct query string
        query_string = urlencode(build_query_items(query_params))
        path = app(app_name)
        if query_string:
            path += f"?{query_string}"

        self.logger.info(f"Updating application '{app_name}'")
        response = self.http.put(path, payload=json.dumps(app_body))
        if response.status_code != 200:
            raise Exception(f"Failed to update application: {response.status_code}, {response.text}")
        return response.json()


    def patch_application(self, patch: dict, query_params: dict = None):
        query_params = query_params or {}
        validate_query_params(query_params, "update_application")

        metadata = patch.get("metadata", {})
        app_name = metadata.get("name")
        if not app_name:
            raise ValueError("metadata.name is required in the patch.")

        current_app = self.get_application(app_name)
        if not current_app:
            raise Exception(f"Application '{app_name}' does not exist.")
        
        updated_app = copy.deepcopy(current_app)
        deep_merge(updated_app, patch)

        query_string = urlencode(build_query_items(query_params))
        path = app(app_name)
        if query_string:
            path += f"?{query_string}"

        self.logger.info(f"Partially updating application '{app_name}'")
        
        response = self.http.put(path, json.dumps(updated_app))
        self.logger.debug(f"Response {response.status_code}: {response.text}")
        if response.status_code != 200:
            raise Exception(f"Failed to patch application: {response.status_code}, {response.text}")
        return response.json()


    def create_or_update_appset(self, appset_name, appset_spec):
        payload = {
            "metadata": {"name": appset_name},
            "spec": appset_spec
        }
        response = self.http.post(path=appsets(), payload=json.dumps(payload))
        self.logger.debug(f"Response {response.status_code}: {response.text}")
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create/update ApplicationSet: {response.status_code}, {response.text}")
        return response.json()

    def sync_application(self, name, revision=None, prune=False, dry_run=False, strategy=None):
        url = f"{self.api_url}{app_sync(name)}"
        self.logger.debug(f"GET {url}")
        sync_options = {
            "revision": revision,
            "prune": prune,
            "dryRun": dry_run
        }
        # remove None values
        if revision:
            sync_options["revision"] = revision

        if strategy in ["apply", "hook"]:
            sync_options["strategy"] = {"type": strategy}

        sync_body = {k: v for k, v in sync_options.items() if v is not None}
        json_body = json.dumps(sync_body)
        self.logger.debug(f"POST {url} with body: {json_body}")
        response = self.http.post(path=app_sync(name), payload=json_body)
        self.logger.debug(f"Response {response.status_code}: {response.text}")
        if response.status_code != 200:
            raise Exception(f"Failed to sync application: {response.status_code}, {response.text}")
        return True, response.json()
