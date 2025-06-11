import copy
import json
import time
from urllib.parse import urlencode
from typing import Dict

from argocd.middleware import ArgoCDResponseError

from .http import HttpClient
from .utils import build_query_items, deep_merge
from .api_routes import app, apps, app_sync, app_manifests, appsets, app_patch_resource
from .logger import get_logger
from .config import API_REQUEST_TIMEOUT
from .validators import validate_query_params, validate_sync_body


class ArgoCDClient:
    def __init__(
        self,
        api_url,
        token,
        proxies,
        timeout=API_REQUEST_TIMEOUT,
        verify_ssl=False,
        debug=False,
    ):
        self.api_url = api_url.rstrip("/")
        self.logger = get_logger(debug=debug)
        self.http = HttpClient(
            base_url=api_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            proxies=proxies,
            timeout=timeout,
            verify_ssl=verify_ssl,
            logger=self.logger,
        )

    def list_applications(self, query_params: dict = None):
        query_params = query_params or {}
        validate_query_params(query_params, "list_applications")
        query_string = urlencode(build_query_items(query_params))
        path = apps()
        if query_string:
            path += f"?{query_string}"

        self.logger.debug(f"GET {self.api_url}{path}")

        return self.http.get(path)

    def get_application(self, name, query_params: dict = None) -> Dict:
        query_params = query_params or {}
        validate_query_params(query_params, "get_application")
        query_string = urlencode(build_query_items(query_params))
        path = app(name)
        if query_string:
            path += f"?{query_string}"

        return self.http.get(path)

    def get_application_manifests(self, name, query_params: dict = None):
        query_params = query_params or {}
        validate_query_params(query_params, "get_manifests")
        query_string = urlencode(build_query_items(query_params))
        path = app_manifests(name)
        if query_string:
            path += f"?{query_string}"

        self.logger.info(f"Getting manifests for application '{name}'")
        return self.http.get(path)
        # try:
        #     response = self.http.get(path)
        #     self.logger.debug(f"Response {response.status_code}: {response.text}")
        #     self.logger.info(
        #         f"get_application_manifests() '{name}' status_code {response['status_code']}"
        #     )
        #     return response
        # except ArgoCDResponseError as e:
        #     self.logger.error(
        #         f"Failed to get manifests for application '{name}' [{e.status_code}]: {e.message}"
        #     )
        #     if e.details:
        #         self.logger.error("Details:", e.details)
        #     return e

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
            raise Exception(
                f"Failed to update application: {response.status_code}, {response.text}"
            )
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
            raise Exception(
                f"Failed to patch application: {response.status_code}, {response.text}"
            )
        return response.json()

    def patch_application_resource(self, name: str, patch: str, query_params: dict):
        if not patch or not isinstance(patch, str):
            raise ValueError("patch must be a raw JSON or YAML string.")

        validate_query_params(query_params, "patch_resource")
        query_string = urlencode(build_query_items(query_params))
        path = app_patch_resource(name)
        if query_string:
            path += f"?{query_string}"

        self.logger.info(
            f"Patching resource for app '{name}' with query: {query_string}"
        )
        response = self.http.post(
            path, payload=json.dumps(patch), content_type="application/json"
        )

        if response.status_code != 200:
            self.logger.error(
                f"Failed to patch resource for application '{name}': {response.status_code}, {response.text}"
            )
            raise Exception(
                f"Failed to patch resource: {response.status_code}, {response.text}"
            )

        return response.json()

    def create_or_update_appset(self, appset_name, appset_spec):
        payload = {"metadata": {"name": appset_name}, "spec": appset_spec}
        response = self.http.post(path=appsets(), payload=json.dumps(payload))
        self.logger.debug(f"Response {response.status_code}: {response.text}")
        if response.status_code not in [200, 201]:
            raise Exception(
                f"Failed to create/update ApplicationSet: {response.status_code}, {response.text}"
            )
        return response.json()

    def get_application_status(self, app_name):
        app = self.get_application(app_name)
        return app.get("data", {}).get("status", {}) if app else {}

    def wait_for_sync(self, app_name, timeout=120, interval=5):
        """
        Wait until it is synced or failed, with a timeout.
        """
        start = time.time()
        while time.time() - start < timeout:
            status = self.get_application_status(app_name)
            sync_status = status.get("sync", {}).get("status")
            health_status = status.get("health", {}).get("status")

            if sync_status == "Synced" and health_status == "Healthy":
                return True
            if sync_status == "Unknown" or health_status == "Degraded":
                return False

            time.sleep(interval)

        return False  # Timeout

    def sync_application_advanced(self, name: str, sync_body: dict):
        """
        Perform a full-featured sync on the application with a structured request body.
        See ArgoCD API docs for all fields. Example:
        {
            "prune": true,
            "dryRun": false,
            "revision": "main",
            "strategy": {
                "apply": {
                    "force": true
                }
            }
        }
        """
        if not isinstance(sync_body, dict):
            raise ValueError("sync_body must be a dictionary")

        path = app_sync(name)
        self.logger.info(f"Syncing application '{name}' with full payload")
        response = self.http.post(path, payload=json.dumps(sync_body))

        if response.status_code != 200:
            raise Exception(
                f"Failed to sync application: {response.status_code}, {response.text}"
            )
        return response.json()

    def sync_application_simplified(
        self,
        name: str,
        revision: str = None,
        force: bool = False,
        prune: bool = False,
        dry_run: bool = False,
        sync_options: list = None,
        wait: bool = True,
        timeout: int = 120,
    ):
        sync_body = {
            "dryRun": dry_run,
            "prune": prune,
            "revision": revision,
            "strategy": {"apply": {"force": force}},
        }

        if sync_options:
            sync_body["syncOptions"] = {"items": sync_options}

        # Clean empty values
        sync_body = {k: v for k, v in sync_body.items() if v is not None}

        self.logger.info(
            f"Starting simplified sync for app '{name}' with body: {json.dumps(sync_body)}"
        )
        result = self.sync_application_advanced(name, sync_body)

        if wait:
            success = self.wait_for_sync(name, timeout)
            if not success:
                raise Exception(
                    f"Application '{name}' did not reach Synced/Healthy state."
                )
            return {
                "synced": True,
                "message": "Sync completed successfully.",
                "result": result,
            }

        return {
            "synced": False,
            "message": "Sync triggered (not waiting).",
            "result": result,
        }

    def sync_application(self, name: str, sync_body: dict):
        if not isinstance(sync_body, dict):
            raise ValueError("sync_body must be a dictionary.")

        validate_sync_body(sync_body)

        self.logger.info(
            f"Triggering sync for \napplication: '{name}' \npayload: {sync_body}"
        )
        self.logger.debug(
            f"Triggering sync for \napplication: '{name}' \npayload: {sync_body}"
        )
        response = self.http.post(app_sync(name), payload=json.dumps(sync_body))
        if response.status_code != 200:
            raise Exception(
                f"Failed to sync application: {response.status_code}, {response.text}"
            )
        return response.json()
