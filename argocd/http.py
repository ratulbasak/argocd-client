import requests
from .middleware import handle_response


class HttpClient:
    def __init__(
        self, base_url, headers, timeout, verify_ssl=True, logger=None, proxies=None
    ):
        self.base_url = base_url.rstrip("/")
        self.headers = headers
        self.verify_ssl = verify_ssl
        self.logger = logger
        self.timeout = timeout
        self.proxies = proxies or {}

    def get(self, path):
        url = f"{self.base_url}{path}"
        resp = requests.get(
            url,
            headers=self.headers,
            verify=self.verify_ssl,
            timeout=self.timeout,
            proxies=self.proxies,
        )
        self._log_response(resp)
        return handle_response(resp)

    def post(self, path, payload, content_type="application/json"):
        url = f"{self.base_url}{path}"
        self.logger.debug(f"POST {url} with body: {payload}")
        headers = self.headers.copy()
        headers["Content-Type"] = content_type
        resp = requests.post(
            url,
            headers=headers,
            data=payload,
            verify=self.verify_ssl,
            timeout=self.timeout,
            proxies=self.proxies,
        )
        self._log_response(resp)
        return handle_response(resp)

    def put(self, path, payload):
        url = f"{self.base_url}{path}"
        self.logger.debug(f"PUT {url} with body: {payload}")
        resp = requests.put(
            url,
            headers=self.headers,
            data=payload,
            verify=self.verify_ssl,
            timeout=self.timeout,
            proxies=self.proxies,
        )
        self._log_response(resp)
        return handle_response(resp)

    def patch(self, path, raw_body, content_type="application/json"):
        url = f"{self.base_url}{path}"
        headers = self.headers.copy()
        headers["Content-Type"] = content_type
        self.logger.debug(f"PATCH {url} with raw body:\n{raw_body}")
        resp = requests.patch(
            url,
            headers=headers,
            data=raw_body,
            verify=self.verify_ssl,
            timeout=self.timeout,
            proxies=self.proxies,
        )
        self._log_response(resp)
        return handle_response(resp)

    def _log_response(self, resp):
        self.logger.debug(f"Response {resp.status_code}: {resp.text}")
