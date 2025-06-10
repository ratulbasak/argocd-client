import requests


class HttpClient:
    def __init__(self, base_url, headers, timeout, verify_ssl=True, logger=None, proxies=None):
        self.base_url = base_url.rstrip("/")
        self.headers = headers
        self.verify_ssl = verify_ssl
        self.logger = logger
        self.timeout = timeout
        self.proxies = proxies or {}

    def get(self, path):
        url = f"{self.base_url}{path}"
        self.logger.info(f"GET {url}")
        resp = requests.get(url, headers=self.headers, verify=self.verify_ssl, timeout=self.timeout)
        self._log_response(resp)
        return resp

    def post(self, path, payload):
        url = f"{self.base_url}{path}"
        self.logger.info(f"POST {url}")
        self.logger.debug(f"POST {url} with body: {payload}")
        resp = requests.post(url, headers=self.headers, data=payload, verify=self.verify_ssl, timeout=self.timeout)
        self._log_response(resp)
        return resp

    def put(self, path, payload):
        url = f"{self.base_url}{path}"
        self.logger.info(f"PUT {url}")
        self.logger.debug(f"PUT {url} with body: {payload}")
        resp = requests.put(url, headers=self.headers, data=payload, verify=self.verify_ssl, timeout=self.timeout)
        self._log_response(resp)
        return resp

    def _log_response(self, resp):
        self.logger.debug(f"Response {resp.status_code}: {resp.text}")
