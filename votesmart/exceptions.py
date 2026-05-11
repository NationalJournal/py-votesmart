class VotesmartApiError(Exception):
    """Exception for Votesmart API errors"""


class VotesmartNotFoundError(VotesmartApiError):
    """Raised when the API returns a 404 with the "no data" body shape:
    ``{"message": "Not Found", "statusCode": 404}``.

    Distinguished from a malformed-URL 404 (Express's default no-route
    handler, which returns ``{"message": "Cannot GET /v1/...", ...}``) so
    list-shaped endpoints can return an empty list while object-shaped
    endpoints still surface a missing resource to the caller.
    """
