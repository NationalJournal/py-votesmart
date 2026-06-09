from ..exceptions import VotesmartApiError


def parse_api_response(response):
    """Parse an API response, raising on error envelopes.

    Detects API errors that come back wrapped in a 2xx HTTP response. The
    REST API 2.0 uses ``{"message": "...", "statusCode": N}`` for errors
    while the legacy API used ``{"error": {"errorMessage": "..."}}`` — we
    handle both for backward compatibility.

    HTTP-level errors (4xx, 5xx) are mapped to the typed exceptions in
    ``VoteSmartAPI._raise_for_status`` *before* this function is called,
    so the ``statusCode`` branch here only fires when an error body is
    smuggled inside a 2xx response.
    """
    if isinstance(response, dict):
        body_status = response.get("statusCode")
        if body_status and body_status >= 400:
            raise VotesmartApiError(
                response.get("message", "Unknown API error"),
                status_code=body_status,
                response_body=response,
            )
        if response.get("error"):
            err = response["error"]
            message = err.get("errorMessage") if isinstance(err, dict) else str(err)
            raise VotesmartApiError(
                message or "Unknown API error",
                response_body=response,
            )
    return response
