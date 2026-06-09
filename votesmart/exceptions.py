class VotesmartApiError(Exception):
    """Base class for all Vote Smart API errors.

    Carries ``status_code`` (the HTTP status from the API, when known) and
    ``response_body`` (the parsed JSON response body, when available). Both
    are ``None`` if the error didn't originate from an HTTP response (e.g.,
    a malformed JWT, a missing auth token).

    The string form of the exception includes ``(HTTP <code>)`` when a
    status code is set and the message doesn't already mention HTTP — so
    callers that just log ``str(exc)`` get a self-diagnosing line.
    """

    def __init__(self, message="", status_code=None, response_body=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self):
        message = super().__str__()
        if self.status_code is not None and "HTTP" not in message:
            return "{} (HTTP {})".format(message, self.status_code)
        return message


class VotesmartNotFoundError(VotesmartApiError):
    """Raised when the API returns a 404 with the "no data" body shape:
    ``{"message": "Not Found", "statusCode": 404}``.

    Distinguished from a malformed-URL 404 (Express's default no-route
    handler, which returns ``{"message": "Cannot GET /v1/...", ...}``) so
    list-shaped endpoints can return an empty list while object-shaped
    endpoints still surface a missing resource to the caller.
    """


class VotesmartRateLimitError(VotesmartApiError):
    """Raised when the API returns 429 Too Many Requests and the configured
    retry budget is exhausted.

    Callers that want to handle rate-limiting specifically (back off
    further at the application layer, requeue the work, etc.) should
    ``except VotesmartRateLimitError`` before the broader
    ``VotesmartApiError``.
    """


class VotesmartServerError(VotesmartApiError):
    """Raised on a 5xx response after the configured retry budget is
    exhausted. Indicates a Vote Smart upstream problem rather than a
    caller bug."""


class VotesmartClientError(VotesmartApiError):
    """Raised on a 4xx response that isn't 404 (no-data) or 429
    (rate-limit). Typically a 400 (bad request), 401 (auth refresh
    didn't fix it), or 403 (forbidden) — i.e., a caller-side problem
    that retrying won't solve."""
