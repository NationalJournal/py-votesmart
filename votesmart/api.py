import base64
import json
import logging
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

from .methods.utils import parse_api_response
from .exceptions import (
    VotesmartApiError,
    VotesmartClientError,
    VotesmartNotFoundError,
    VotesmartRateLimitError,
    VotesmartServerError,
)
from . import methods


logger = logging.getLogger(__name__)


# HTTP status codes that are worth retrying. 429 is the primary motivator
# (Vote Smart rate-limits aggressively); the 5xx set covers upstream
# blips that typically resolve on a second attempt. 4xx codes other than
# 429 are caller-side problems that retrying won't fix.
TRANSIENT_STATUS_CODES = frozenset({429, 502, 503, 504})


class VoteSmartAPI:
    """Client for the Vote Smart REST API 2.0.

    Authentication uses email/password to obtain a JWT access token from
    the public auth endpoint. Callers may pass in a cached token to avoid
    re-authenticating on every instantiation.

    Args:
        email: Account email for Vote Smart API.
        password: Account password for Vote Smart API.
        access_token: Optional cached JWT token string.
        token_validity_period: Minimum remaining seconds before the token
            is considered expired and a new one is requested. Defaults
            to 3600 (1 hour).
        rate_limit: Maximum requests per second for the built-in
            in-process limiter. Ignored if ``rate_limiter`` is supplied.
            Defaults to None (no in-process limiting).
        rate_limiter: Optional callable ``f() -> None`` that blocks until
            the next request is allowed. Takes precedence over
            ``rate_limit``. Use this to plug in a distributed limiter
            (e.g. Redis-backed token bucket) shared across processes.
        max_retries: Number of retries to attempt on transient HTTP
            errors (429, 502, 503, 504). Defaults to 5. Set to 0 to
            disable.
        retry_initial_backoff: Base delay (seconds) for the first retry
            when no Retry-After header is present. Doubles on each
            subsequent retry, capped at ``retry_max_backoff``. Defaults
            to 1.0.
        retry_max_backoff: Upper bound (seconds) on the computed
            exponential backoff. Defaults to 60.0.
        retry_backoff_jitter: Multiplicative jitter applied to backoff
            delays, in the range ``[1 - jitter, 1 + jitter]``. Defaults
            to 0.5 (i.e. ±50%). Set to 0.0 to disable.
        retry_after_max: Upper bound (seconds) on a server-supplied
            Retry-After value. Defends against absurd or hostile values.
            Defaults to 300.0 (5 minutes).
    """

    AUTH_URL = "https://app.votesmart-api.org/auth/login"
    BASE_URL = "https://app.votesmart-api.org"

    def __init__(
        self,
        email=None,
        password=None,
        access_token=None,
        token_validity_period=3600,
        rate_limit=None,
        rate_limiter=None,
        max_retries=5,
        retry_initial_backoff=1.0,
        retry_max_backoff=60.0,
        retry_backoff_jitter=0.5,
        retry_after_max=300.0,
    ):
        if not email or not password:
            raise ValueError("Vote Smart API email and password are required")

        self._email = email
        self._password = password
        self._token_validity_period = token_validity_period
        self._access_token = access_token
        self._token_changed = False
        self._method_cache = {}

        # Rate limiting
        self._rate_limit = rate_limit
        self._rate_limiter = rate_limiter
        self._last_request_time = 0

        # Retry-with-backoff config
        self._max_retries = max_retries
        self._retry_initial_backoff = retry_initial_backoff
        self._retry_max_backoff = retry_max_backoff
        self._retry_backoff_jitter = retry_backoff_jitter
        self._retry_after_max = retry_after_max

        # Validate or refresh the token
        if not self._is_token_valid():
            self._authenticate()

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    @property
    def access_token(self):
        """Return the current access token. If it was refreshed during
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
                "Authentication failed: {}".format(response.text),
                status_code=response.status_code,
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

        Retries transparently on transient errors (429, 502, 503, 504),
        honoring the server's ``Retry-After`` header when present and
        falling back to exponential backoff with jitter otherwise.
        Permanent errors (400, 401-after-refresh, 403, etc.) raise the
        appropriate typed exception immediately.

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

        backoff = self._retry_initial_backoff
        last_response = None

        for attempt in range(self._max_retries + 1):
            # Respect the configured rate limit before EVERY attempt.
            # Retry delays are additive on top of the local rate budget.
            self._wait_for_rate_limit()

            response = self._send_with_auth_refresh(url, params)
            last_response = response

            # 404 is never retried — it's either "no data" (a real,
            # actionable result for list-shaped callers) or "wrong URL"
            # (a caller bug). Both cases raise.
            if response.status_code == 404:
                self._raise_404(response, url)

            if response.status_code in TRANSIENT_STATUS_CODES:
                if attempt < self._max_retries:
                    delay = self._compute_retry_delay(response, backoff)
                    logger.info(
                        "VoteSmart %s returned %d; sleeping %.2fs before retry "
                        "(attempt %d/%d)",
                        url,
                        response.status_code,
                        delay,
                        attempt + 1,
                        self._max_retries,
                    )
                    time.sleep(delay)
                    backoff = min(backoff * 2, self._retry_max_backoff)
                    continue
                logger.warning(
                    "VoteSmart %s returned %d; retries exhausted after %d attempts",
                    url,
                    response.status_code,
                    self._max_retries + 1,
                )
                # Fall through to raise

            if response.status_code >= 400:
                self._raise_for_status(response, url)  # raises

            # 2xx — parse and return. parse_api_response handles the case
            # where an error envelope is smuggled inside a 2xx response.
            try:
                data = response.json()
            except ValueError:
                raise VotesmartApiError(
                    "Invalid JSON response from API",
                    status_code=response.status_code,
                )
            return parse_api_response(data)

        # Defensive: the for-else equivalent. We should not reach here in
        # practice — either we returned successfully or one of the raise
        # paths above fired. If we do, treat the last response as a
        # failure so we don't silently return None.
        if last_response is not None:
            self._raise_for_status(last_response, url)
        raise VotesmartApiError("Retry loop completed without a response")

    # ------------------------------------------------------------------
    # Retry / rate-limit helpers
    # ------------------------------------------------------------------

    def _send_with_auth_refresh(self, url, params):
        """Send a single request. On 401, re-authenticate and retry once
        with the new token. Returns the final response (which may itself
        still be a 401 if re-auth didn't fix it; the caller decides what
        to do with that)."""
        headers = {"Authorization": "Bearer {}".format(self._access_token)}
        self._last_request_time = time.time()
        response = requests.get(url, params=params or {}, headers=headers)

        if response.status_code == 401:
            self._authenticate()
            headers = {
                "Authorization": "Bearer {}".format(self._access_token)
            }
            self._last_request_time = time.time()
            response = requests.get(url, params=params or {}, headers=headers)

        return response

    def _wait_for_rate_limit(self):
        """Block until the configured limiter allows the next request.

        If a custom ``rate_limiter`` callable was supplied, it takes
        precedence. Otherwise the built-in in-process limiter sleeps to
        keep us under ``rate_limit`` requests per second. No limiter
        configured means no waiting.
        """
        if self._rate_limiter is not None:
            self._rate_limiter()
            return
        if self._rate_limit:
            min_interval = 1.0 / self._rate_limit
            elapsed = time.time() - self._last_request_time
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)

    def _compute_retry_delay(self, response, default_backoff):
        """Return the delay (seconds) before the next retry attempt.

        Prefers a server-supplied ``Retry-After`` header (capped at
        ``retry_after_max``). Falls back to ``default_backoff`` with
        multiplicative jitter applied.
        """
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            parsed = self._parse_retry_after(retry_after)
            if parsed is not None:
                return min(parsed, self._retry_after_max)
        if self._retry_backoff_jitter:
            jitter_factor = 1.0 + random.uniform(
                -self._retry_backoff_jitter, self._retry_backoff_jitter
            )
            return max(0.0, default_backoff * jitter_factor)
        return default_backoff

    @staticmethod
    def _parse_retry_after(value):
        """Parse a Retry-After header value.

        Per RFC 7231 §7.1.3 it's either:
          - delta-seconds (a non-negative integer), or
          - HTTP-date (RFC 7231 §7.1.1.1).

        Returns the delay in seconds, or ``None`` if unparseable.
        """
        value = value.strip()
        try:
            return max(0.0, float(value))
        except ValueError:
            pass
        try:
            dt = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        if dt is None:
            return None
        now = datetime.now(timezone.utc) if dt.tzinfo else datetime.now()
        return max(0.0, (dt - now).total_seconds())

    # ------------------------------------------------------------------
    # Error-mapping helpers
    # ------------------------------------------------------------------

    def _raise_404(self, response, url):
        """Distinguish 'no data' 404s from malformed-URL 404s.

        - Body shape ``{"message": "Not Found", "statusCode": 404}`` →
          ``VotesmartNotFoundError``. The route exists but VS has no
          data for the query. List-shaped callers catch this and return
          an empty list.
        - Any other 404 (Express's "Cannot GET /v1/...", an HTML page
          from infrastructure, empty body, unrecognized shape) →
          ``VotesmartApiError``. Surfaces caller bugs and upstream
          oddities instead of silently treating them as "no data."
        """
        try:
            body = response.json()
        except ValueError:
            body = None
        if (
            isinstance(body, dict)
            and body.get("message") == "Not Found"
            and "error" not in body
        ):
            raise VotesmartNotFoundError(
                "Resource not found: {}".format(url),
                status_code=404,
                response_body=body,
            )
        raise VotesmartApiError(
            "Endpoint not found: {}".format(url),
            status_code=404,
            response_body=body,
        )

    def _raise_for_status(self, response, url):
        """Map a >= 400 response to a typed exception and raise.

        - 429 → ``VotesmartRateLimitError``
        - 5xx → ``VotesmartServerError``
        - other 4xx (except 404, handled separately) →
          ``VotesmartClientError``
        - anything else (shouldn't happen given the caller's 2xx guard) →
          ``VotesmartApiError``

        All carry ``status_code`` and ``response_body`` for callers that
        want to introspect.
        """
        code = response.status_code
        try:
            body = response.json()
        except ValueError:
            body = None
        message = self._extract_error_message(body) or self._fallback_text(response)

        if code == 429:
            raise VotesmartRateLimitError(
                "Rate limited by VoteSmart: {}".format(message),
                status_code=code,
                response_body=body,
            )
        if 500 <= code < 600:
            raise VotesmartServerError(
                "VoteSmart server error: {}".format(message),
                status_code=code,
                response_body=body,
            )
        if 400 <= code < 500:
            raise VotesmartClientError(
                "VoteSmart client error: {}".format(message),
                status_code=code,
                response_body=body,
            )
        raise VotesmartApiError(
            "Unexpected response status: {}".format(message),
            status_code=code,
            response_body=body,
        )

    @staticmethod
    def _extract_error_message(body):
        """Pull a human-readable message from a parsed JSON error body."""
        if not isinstance(body, dict):
            return None
        message = body.get("message")
        if message:
            return message
        err = body.get("error")
        if isinstance(err, dict):
            return err.get("errorMessage")
        if isinstance(err, str):
            return err
        return None

    @staticmethod
    def _fallback_text(response):
        """Use the raw response text (truncated) when no JSON body."""
        text = (response.text or "").strip()
        if text:
            return text[:500]
        return "no response body"

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
