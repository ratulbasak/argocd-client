import json
from argocd.client import ArgoCDClient
from dotenv import load_dotenv
import os
import urllib3

from argocd.middleware import ArgoCDResponseError
from argocd.utils import load_yaml

urllib3.disable_warnings()

load_dotenv()


def main():
    result = dict(changed=False, app={})

    app_name = "guestbook"
    metaapp_name = "guesbook-metaapp"
    app_patch = """
        metadata: 
        labels: 
            nar-instance-id: "111-1"
        spec:
        source:
            repoURL: https://github.com/ratulbasak/argo_ui_extensions.git
            path: deployments/guestbook
            targetRevision: test
        syncPolicy:
            syncOptions:
            - ApplyOutOfSyncOnly=true
        """

    try:
        client = ArgoCDClient(
            api_url=os.getenv("ARGOCD_API_URL"),
            token=os.getenv("ARGOCD_AUTH_TOKEN"),
            verify_ssl=os.getenv("ARGOCD_VERIFY_SSL"),
            timeout=10,
            proxies={"http": "", "https": ""},
            debug=False,
        )

        ## LIST APPLICATIONS
        apps = client.list_applications({"project": ["default"], "refresh": "hard"})

        # print(apps)

        ## GET SINGLE APPLICATION
        app = client.get_application(
            name=app_name, query_params={"project": ["default"], "refresh": "hard"}
        )
        # print(app)
        # print(f"App get successfully.")

        ## UPDATE APPLICATION
        # app["spec"]["source"]["targetRevision"] = "test"
        # app_update_body = {
        #     "metadata": {
        #         "name": "my-app",
        #         "labels": {
        #             "env": "prod"
        #         }
        #     },
        #     "spec": {
        #         "project": "default",
        #         "source": {
        #             "repoURL": "https://github.com/org/repo.git",
        #             "path": "app",
        #             "targetRevision": "v1.0.0"
        #         },
        #         "destination": {
        #             "server": "https://kubernetes.default.svc",
        #             "namespace": "default"
        #         }
        #     }
        # }

        # client.update_application(app, {"validate": True})

        ## GET APP MANIFESTS
        # manifests = client.get_application_manifests(
        #     metaapp_name,
        #     {
        #         "revision": "6b992b7",
        #         "project": "default",
        #         # "revisions": ["v1.2.3", "v1.2.2"]
        #     },
        # )
        # print(manifests)
        # manifests = manifests["manifests"]

        # for manifest in manifests:
        #     manifest = json.loads(manifest)
        #     if manifest["kind"] == "Deployment":
        #         print(manifest)

        # for line in manifests.splitlines():
        #     if line.strip().startswith("image: "):
        #         image = line.replace("image: ", "").strip().strip('"')
        #         print(f"image: {image}")

        ## PATCH APPLICATION
        # patch_data = load_yaml(app_patch)
        # patch = {
        #     "metadata": {
        #         "name": "guestbook",
        #         "labels": {
        #             "env": "staging",
        #             "nar-instance-id": "111-1"
        #         }
        #     },
        #     "spec": {
        #         "source": {
        #             "targetRevision": "test"
        #         }
        #     }
        # }
        # client.patch_application(patch, {"validate": True})
        # print(f"App patched successfully.")

        ## PATCH SPECIFIC APPLICATION RESOURCE
        query = {
            "namespace": "guestbook",
            "resourceName": "hello-world-deployment1",
            "version": "v1",
            "group": "apps",
            "kind": "Deployment",
            "patchType": "application/merge-patch+json",
        }

        patch_body = '{"spec": {"replicas": 3}}'

        client.patch_application_resource(app_name, patch_body, query)

        ## SYNC APPLICATION
        # app = client.sync_application(
        #   app_name=app_name,
        #   prune=True,
        #   dry_run=False,
        #   strategy="apply"
        # )

        sync_request = {
            "dryRun": True,
            "prune": True,
            "revision": "test",
            "strategy": {"apply": {"force": False}},
            "syncOptions": {
                "items": [
                    "ApplyOutOfSyncOnly=true",
                    "ServerSideApply=true",
                    "Replace=true",
                ]
            },
        }

        # result = client.sync_application(app_name, sync_request)
        # print(result)
        client.sync_application_simplified(
            name=app_name,
            # revision="test",
            force=False,
            prune=True,
            dry_run=False,
            sync_options=["CreateNamespace=true"],
            wait=True,
            timeout=90,
        )
        print(f"App synced successfully.")

    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
