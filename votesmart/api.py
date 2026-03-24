import base64
import json
import time

import requests

from .methods.utils import parse_api_response
from .exceptions import VotesmartApiError
from . import methods


class VoteSmartAPI:
    """Client for the Vote Smart REST API 2.0.

    Authentication uses email/password to obtain a JWT access token from
    the public auth endpoint.  Callers may pass in a cached token to avoid
    re-authenticating on every instantiation.

    Args:
        email: Account email for Vote Smart API.
        password: Account password for Vote Smart API.
        access_token: Optional cached JWT token string.
        token_validity_period: Minimum remaining seconds before the token
            is considered expired and a new one is requested.  Defaults to
            3600 (1 hour).
    """

    AUTH_URL = "https://app.votesmart-api.org/auth/login"
    BASE_URL = "https://app.votesmart-api.org"

    def __init__(self, email=None, password=None, access_token=None,
                 token_validity_period=3600):
        if not email or not password:
            raise ValueError("Vote Smart API email and password are required")

        self._email = email
        self._password = password
        self._token_validity_period = token_validity_period
        self._access_token = access_token
        self._token_changed = False
        self._method_cache = {}

        # Validate or refresh the token
        if not self._is_token_valid():
            self._authenticate()

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    @property
    def access_token(self):
        """Return the current access token.  If it was refreshed during
        init or an API call, the caller should cache the new value."""
        return self._access_token

    @property
    def token_changed(self):
        """True if the token was refreshed since instantiation."""
        return self._token_changed

    def _is_token_valid(self):
        """Check whether the current token exists and has enough remaining
        lifetime (at least ``token_validity_period`` seconds)."""
        if not self._access_token:
            return False
        try:
            payload = self._decode_jwt_payload(self._access_token)
            exp = payload.get("exp", 0)
            return (exp - time.time()) > self._token_validity_period
        except Exception:
            return False

    def _authenticate(self):
        """Obtain a new access token from the auth endpoint."""
        response = requests.post(
            self.AUTH_URL,
            json={"email": self._email, "password": self._password},
        )
        if response.status_code not in (200, 201):
            raise VotesmartApiError(
                "Authentication failed (HTTP {}): {}".format(
                    response.status_code, response.text
                )
            )
        data = response.json()
        token = data.get("accessToken") or data.get("access_token")
        if not token:
            raise VotesmartApiError(
                "Authentication response did not contain an access token"
            )
        self._access_token = token
        self._token_changed = True

    @staticmethod
    def _decode_jwt_payload(token):
        """Decode the payload of a JWT without verifying the signature."""
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
        # Add padding for base64
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes)

    # ------------------------------------------------------------------
    # API call
    # ------------------------------------------------------------------

    def api_call(self, endpoint, params=None):
        """Make an authenticated GET request to the Vote Smart API.

        Args:
            endpoint: API endpoint path (e.g. "v1/elections" or
                "v1/candidates/by-election").
            params: Optional dict of query parameters.

        Returns:
            Parsed JSON response dict.
        """
        # Refresh token if needed before making the call
        if not self._is_token_valid():
            self._authenticate()

        url = "{}/{}".format(self.BASE_URL, endpoint.lstrip("/"))
        headers = {"Authorization": "Bearer {}".format(self._access_token)}

        response = requests.get(url, params=params or {}, headers=headers)

        if response.status_code == 401:
            # Token may have expired mid-session — retry once
            self._authenticate()
            headers = {"Authorization": "Bearer {}".format(self._access_token)}
            response = requests.get(url, params=params or {}, headers=headers)

        if response.status_code == 404:
            raise VotesmartApiError(
                "Endpoint not found: {} (HTTP 404)".format(url)
            )

        # Check for HTTP errors before attempting JSON parse
        if response.status_code >= 400:
            try:
                data = response.json()
            except ValueError:
                raise VotesmartApiError(
                    "API error (HTTP {}): {}".format(
                        response.status_code, response.text[:500]
                    )
                )
            return parse_api_response(data)

        try:
            data = response.json()
        except ValueError:
            raise VotesmartApiError("Invalid JSON response from API")

        return parse_api_response(data)

    # ------------------------------------------------------------------
    # Method accessors (cached)
    # ------------------------------------------------------------------

    def _get_method(self, name, cls):
        if name not in self._method_cache:
            self._method_cache[name] = cls(self)
        return self._method_cache[name]

    @property
    def Address(self):
        return self._get_method('Address', methods.Address)

    @property
    def CandidateBio(self):
        return self._get_method('CandidateBio', methods.CandidateBio)

    @property
    def Candidates(self):
        return self._get_method('Candidates', methods.Candidates)

    @property
    def Committee(self):
        return self._get_method('Committee', methods.Committee)

    @property
    def District(self):
        return self._get_method('District', methods.District)

    @property
    def Election(self):
        return self._get_method('Election', methods.Election)

    @property
    def Leadership(self):
        return self._get_method('Leadership', methods.Leadership)

    @property
    def Local(self):
        return self._get_method('Local', methods.Local)

    @property
    def Measure(self):
        return self._get_method('Measure', methods.Measure)

    @property
    def Npat(self):
        return self._get_method('Npat', methods.Npat)

    @property
    def Office(self):
        return self._get_method('Office', methods.Office)

    @property
    def Officials(self):
        return self._get_method('Officials', methods.Officials)

    @property
    def State(self):
        return self._get_method('State', methods.State)

    @property
    def Rating(self):
        return self._get_method('Rating', methods.Rating)

    @property
    def Votes(self):
        return self._get_method('Votes', methods.Votes)
