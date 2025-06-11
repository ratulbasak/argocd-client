import logging

logger = logging.getLogger("argocd_client")

REDACT_HEADERS = {"authorization", "cookie", "set-cookie"}


def redact_headers(headers: dict) -> dict:
    return {
        k: ("***REDACTED***" if k.lower() in REDACT_HEADERS else v)
        for k, v in headers.items()
    }


class ArgoCDResponseError(Exception):
    def __init__(
        self,
        status_code,
        message,
        details=None,
        raw=None,
        method=None,
        url=None,
        request_headers=None,
    ):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        self.raw = raw
        self.method = method
        self.url = url
        self.request_headers = request_headers or {}
        super().__init__(f"[{status_code}] {message} [{method} {url}]")

    def __str__(self):
        return (
            f"[{self.status_code}] {self.message}\n"
            f"Request: {self.method} {self.url}\n"
            f"Details: {self.details}"
        )


def handle_response(resp):
    content_type = resp.headers.get("Content-Type", "")
    status = resp.status_code
    raw_text = resp.text
    request = resp.request

    method = request.method
    url = request.url
    headers = redact_headers(dict(request.headers))

    logger.info(f"{method} {url} {status}")
    logger.info(f"Request Headers: {dict(headers)}")
    logger.info(f"Response Headers: {dict(resp.headers)}")

    if 200 <= status < 300:
        if "application/json" in content_type:
            try:
                # print(resp.json())
                success_body = resp.json()
                return {"success": True, "status_code": status, "data": resp.json()}
            except Exception:
                logger.warning(
                    "Response claims JSON but failed to parse. Returning raw body."
                )

        return {"success": True, "status_code": status, "data": raw_text}

    # Error handling
    try:
        error_body = resp.json()
        message = error_body.get("message") or error_body.get("error") or resp.reason
        details = {
            "code": error_body.get("code"),
            "error": error_body.get("error"),
            "details": error_body.get("details"),
        }
    except Exception:
        message = resp.reason or "Unknown error"
        details = {}
        logger.error("Failed to parse error response: %s", raw_text)

    raise ArgoCDResponseError(
        status_code=status,
        message=message,
        details=details,
        raw=raw_text,
        method=method,
        url=url,
        request_headers=headers,
    )
