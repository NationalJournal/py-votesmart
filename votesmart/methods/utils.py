from ..exceptions import VotesmartApiError


def parse_api_response(response):
    """Parse an API response, raising on errors.

    The new REST API 2.0 returns errors as {"message": "...", "statusCode": N}
    while the legacy API used {"error": {"errorMessage": "..."}}.
    """
    # New API error format
    if isinstance(response, dict):
        if response.get("statusCode") and response["statusCode"] >= 400:
            raise VotesmartApiError(
                response.get("message", "Unknown API error")
            )
        # Legacy error format (kept for compatibility)
        if response.get("error"):
            raise VotesmartApiError(response["error"]["errorMessage"])
    return response
