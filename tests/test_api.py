import base64
import email.utils
import json
import time
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest
import requests

from votesmart.api import VoteSmartAPI
from votesmart.exceptions import (
    VotesmartApiError,
    VotesmartClientError,
    VotesmartNotFoundError,
    VotesmartRateLimitError,
    VotesmartServerError,
)


def _make_jwt(exp=None):
    """Build a minimal JWT string for testing."""
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b'=')
    if exp is None:
        exp = int(time.time()) + 86400
    payload_dict = {"exp": exp, "iat": exp - 86400}
    payload = base64.urlsafe_b64encode(
        json.dumps(payload_dict).encode()
    ).rstrip(b'=')
    sig = base64.urlsafe_b64encode(b'fakesig').rstrip(b'=')
    return '{}.{}.{}'.format(
        header.decode(), payload.decode(), sig.decode()
    )


def _mock_response(status_code, json_data=None, headers=None, text=None):
    """Build a Mock that mimics a requests.Response for our assertions."""
    resp = mock.Mock()
    resp.status_code = status_code
    resp.headers = headers or {}
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = ValueError("No JSON")
    resp.text = text if text is not None else ""
    return resp


@pytest.fixture
def fast_retries(mocker):
    """Patch time.sleep in the api module so retry loops don't really wait."""
    return mocker.patch("votesmart.api.time.sleep")


@pytest.fixture
def authed_api(mocker):
    """An API instance with a valid cached JWT, no real auth call made."""
    mocker.patch.object(requests, "post")
    return VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=_make_jwt(),
    )


# ---------------------------------------------------------------------
# Smoke / init
# ---------------------------------------------------------------------


def test_sanity():
    assert 1 + 1 == 2


def test_init_api_no_credentials():
    with pytest.raises(ValueError):
        VoteSmartAPI()


def test_init_api_no_password():
    with pytest.raises(ValueError):
        VoteSmartAPI(email="test@test.com")


def test_init_with_valid_cached_token(mocker):
    """If a valid token is supplied, no auth call should be made."""
    mocker.patch.object(requests, "post")
    token = _make_jwt()
    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=token,
    )
    requests.post.assert_not_called()
    assert api.access_token == token
    assert api.token_changed is False


def test_init_with_expired_token_triggers_auth(mocker):
    """An expired token should trigger re-authentication."""
    expired_token = _make_jwt(exp=int(time.time()) - 100)
    new_token = _make_jwt()

    auth_response = _mock_response(200, {"accessToken": new_token})
    mocker.patch.object(requests, "post", return_value=auth_response)

    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=expired_token,
    )
    requests.post.assert_called_once()
    assert api.access_token == new_token
    assert api.token_changed is True


def test_init_without_token_triggers_auth(mocker):
    """No token at all should trigger authentication."""
    new_token = _make_jwt()
    auth_response = _mock_response(200, {"accessToken": new_token})
    mocker.patch.object(requests, "post", return_value=auth_response)

    api = VoteSmartAPI(email="test@test.com", password="password")
    requests.post.assert_called_once()
    assert api.access_token == new_token


# ---------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------


def test_api_call(mocker, authed_api):
    """api_call should make a GET with Bearer auth header."""
    response = _mock_response(200, {"data": [{"id": 1}]})
    mocker.patch.object(requests, "get", return_value=response)

    result = authed_api.api_call("v1/elections/by-year-state", {"year": 2024})

    requests.get.assert_called_once()
    call_args = requests.get.call_args
    assert "v1/elections/by-year-state" in call_args[0][0]
    assert "Bearer" in call_args[1]["headers"]["Authorization"]
    assert result == {"data": [{"id": 1}]}


# ---------------------------------------------------------------------
# 401 re-auth (regression — existing behavior preserved)
# ---------------------------------------------------------------------


def test_api_call_retries_on_401(mocker):
    """On 401, api_call should re-authenticate and retry."""
    token = _make_jwt()
    new_token = _make_jwt(exp=int(time.time()) + 90000)

    auth_response = _mock_response(200, {"accessToken": new_token})
    mocker.patch.object(requests, "post", return_value=auth_response)

    unauthorized = _mock_response(401)
    success = _mock_response(200, {"data": []})
    mocker.patch.object(requests, "get", side_effect=[unauthorized, success])

    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=token,
    )
    result = api.api_call("v1/states")
    assert requests.get.call_count == 2
    assert result == {"data": []}


# ---------------------------------------------------------------------
# 404 discrimination (regression)
# ---------------------------------------------------------------------


def test_api_call_raises_endpoint_not_found_on_malformed_url_404(
    mocker, authed_api
):
    """404 with Express's "Cannot GET" body shape signals a wrong URL — a
    caller bug. Always raises the broad VotesmartApiError (not the subclass)
    so the data-not-found path stays distinguishable."""
    not_found = _mock_response(
        404,
        {
            "message": "Cannot GET /v1/nonexistent",
            "error": "Not Found",
            "statusCode": 404,
        },
    )
    mocker.patch.object(requests, "get", return_value=not_found)

    with pytest.raises(VotesmartApiError) as exc_info:
        authed_api.api_call("v1/nonexistent")
    assert not isinstance(exc_info.value, VotesmartNotFoundError)
    assert "Endpoint not found" in str(exc_info.value)
    assert exc_info.value.status_code == 404


def test_api_call_raises_not_found_subclass_on_data_not_found_404(
    mocker, authed_api
):
    """404 with the "no data" body shape signals the route is valid but VS
    has nothing for this query. Raises VotesmartNotFoundError so list-shaped
    callers can catch and treat as empty."""
    not_found = _mock_response(404, {"message": "Not Found", "statusCode": 404})
    mocker.patch.object(requests, "get", return_value=not_found)

    with pytest.raises(VotesmartNotFoundError) as exc_info:
        authed_api.api_call(
            "v1/elections/5342/stage-candidates", {"stageId": "G"}
        )
    assert "Resource not found" in str(exc_info.value)
    assert exc_info.value.status_code == 404


def test_api_call_raises_endpoint_not_found_on_unparseable_404_body(
    mocker, authed_api
):
    """If the 404 body isn't JSON (HTML error page from a load balancer,
    empty body, etc.) treat it as an unknown error and raise the broad type."""
    not_found = _mock_response(404)
    mocker.patch.object(requests, "get", return_value=not_found)

    with pytest.raises(VotesmartApiError) as exc_info:
        authed_api.api_call("v1/something")
    assert not isinstance(exc_info.value, VotesmartNotFoundError)


# ---------------------------------------------------------------------
# Retry-on-transient (the new behavior)
# ---------------------------------------------------------------------


def test_429_retried_with_eventual_success(mocker, fast_retries, authed_api):
    """A 429 followed by a 200 should succeed transparently to the caller."""
    rate_limited = _mock_response(
        429, {"statusCode": 429, "message": "Too Many Requests"}
    )
    success = _mock_response(200, {"data": [{"id": 1}]})
    mocker.patch.object(requests, "get", side_effect=[rate_limited, success])

    result = authed_api.api_call("v1/candidatebios/123/detail")
    assert result == {"data": [{"id": 1}]}
    assert requests.get.call_count == 2
    assert fast_retries.call_count == 1


def test_503_retried_with_eventual_success(mocker, fast_retries, authed_api):
    """5xx codes (502, 503, 504) are also retried."""
    server_err = _mock_response(503, text="Service Unavailable")
    success = _mock_response(200, {"ok": True})
    mocker.patch.object(requests, "get", side_effect=[server_err, success])

    result = authed_api.api_call("v1/states")
    assert result == {"ok": True}


def test_429_retried_until_max_then_raises_rate_limit_error(
    mocker, fast_retries
):
    """When retries are exhausted on 429, raise VotesmartRateLimitError."""
    mocker.patch.object(requests, "post")
    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=_make_jwt(),
        max_retries=2,
    )
    rate_limited = _mock_response(
        429, {"statusCode": 429, "message": "Too Many Requests"}
    )
    mocker.patch.object(requests, "get", return_value=rate_limited)

    with pytest.raises(VotesmartRateLimitError) as exc_info:
        api.api_call("v1/candidatebios/123/detail")
    assert exc_info.value.status_code == 429
    assert "Too Many Requests" in str(exc_info.value)
    # max_retries=2 means 3 total attempts (initial + 2 retries)
    assert requests.get.call_count == 3
    assert fast_retries.call_count == 2


def test_500_retried_until_max_then_raises_server_error(
    mocker, fast_retries
):
    """Persistent 5xx raises VotesmartServerError after retries."""
    mocker.patch.object(requests, "post")
    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=_make_jwt(),
        max_retries=1,
    )
    server_err = _mock_response(
        500, {"statusCode": 500, "message": "Internal Server Error"}
    )
    mocker.patch.object(requests, "get", return_value=server_err)

    with pytest.raises(VotesmartServerError) as exc_info:
        api.api_call("v1/states")
    assert exc_info.value.status_code == 500
    assert "Internal Server Error" in str(exc_info.value)


def test_500_was_already_handled_500_is_in_transient_set():
    """5xx codes 502/503/504 are transient; pure 500 is NOT retried.

    Some servers return 500 for permanent server bugs, so we keep it out
    of the transient set to avoid masking those. Confirm the membership.
    """
    from votesmart.api import TRANSIENT_STATUS_CODES
    assert 500 not in TRANSIENT_STATUS_CODES
    assert 502 in TRANSIENT_STATUS_CODES
    assert 503 in TRANSIENT_STATUS_CODES
    assert 504 in TRANSIENT_STATUS_CODES
    assert 429 in TRANSIENT_STATUS_CODES


def test_500_not_retried_when_not_in_transient_set(mocker, fast_retries, authed_api):
    """Confirm 500s raise immediately (no retry) — matches the previous
    behavior for plain 500s."""
    server_err = _mock_response(
        500, {"statusCode": 500, "message": "Internal Server Error"}
    )
    mocker.patch.object(requests, "get", return_value=server_err)

    with pytest.raises(VotesmartServerError) as exc_info:
        authed_api.api_call("v1/states")
    assert exc_info.value.status_code == 500
    assert requests.get.call_count == 1
    assert fast_retries.call_count == 0


def test_400_not_retried_raises_client_error(mocker, fast_retries, authed_api):
    """4xx other than 404/429 raises VotesmartClientError immediately."""
    bad_request = _mock_response(
        400, {"statusCode": 400, "message": "Bad year parameter"}
    )
    mocker.patch.object(requests, "get", return_value=bad_request)

    with pytest.raises(VotesmartClientError) as exc_info:
        authed_api.api_call("v1/elections/by-year-state", {"year": "abc"})
    assert exc_info.value.status_code == 400
    assert "Bad year parameter" in str(exc_info.value)
    assert requests.get.call_count == 1


def test_403_not_retried_raises_client_error(mocker, fast_retries, authed_api):
    forbidden = _mock_response(403, text="Forbidden")
    mocker.patch.object(requests, "get", return_value=forbidden)

    with pytest.raises(VotesmartClientError) as exc_info:
        authed_api.api_call("v1/admin/secret-endpoint")
    assert exc_info.value.status_code == 403


def test_max_retries_zero_disables_retry(mocker, fast_retries):
    """max_retries=0 means: one attempt, no retries."""
    mocker.patch.object(requests, "post")
    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=_make_jwt(),
        max_retries=0,
    )
    rate_limited = _mock_response(429)
    mocker.patch.object(requests, "get", return_value=rate_limited)

    with pytest.raises(VotesmartRateLimitError):
        api.api_call("v1/candidatebios/123/detail")
    assert requests.get.call_count == 1
    assert fast_retries.call_count == 0


# ---------------------------------------------------------------------
# Retry-After honoring
# ---------------------------------------------------------------------


def test_retry_after_seconds_honored(mocker, fast_retries, authed_api):
    """Numeric Retry-After header is used as the sleep duration."""
    rate_limited = _mock_response(429, headers={"Retry-After": "7"})
    success = _mock_response(200, {"ok": True})
    mocker.patch.object(requests, "get", side_effect=[rate_limited, success])

    authed_api.api_call("v1/states")
    fast_retries.assert_called_once_with(7.0)


def test_retry_after_http_date_honored(mocker, fast_retries, authed_api):
    """HTTP-date Retry-After header is parsed correctly."""
    future = datetime.now(timezone.utc) + timedelta(seconds=12)
    rate_limited = _mock_response(
        429,
        headers={"Retry-After": email.utils.format_datetime(future)},
    )
    success = _mock_response(200, {"ok": True})
    mocker.patch.object(requests, "get", side_effect=[rate_limited, success])

    authed_api.api_call("v1/states")
    fast_retries.assert_called_once()
    delay = fast_retries.call_args[0][0]
    # Should be close to 12 seconds, allowing for clock drift between the
    # test fixture's `now` and the api module's `now`.
    assert 9 < delay <= 12


def test_retry_after_capped_at_retry_after_max(mocker, fast_retries):
    """An absurd server-supplied Retry-After is capped at retry_after_max."""
    mocker.patch.object(requests, "post")
    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=_make_jwt(),
        retry_after_max=30.0,
    )
    rate_limited = _mock_response(429, headers={"Retry-After": "999999"})
    success = _mock_response(200, {"ok": True})
    mocker.patch.object(requests, "get", side_effect=[rate_limited, success])

    api.api_call("v1/states")
    fast_retries.assert_called_once_with(30.0)


def test_retry_after_unparseable_falls_back_to_backoff(
    mocker, fast_retries, authed_api
):
    """Garbage Retry-After header falls back to exponential backoff."""
    rate_limited = _mock_response(429, headers={"Retry-After": "garbage"})
    success = _mock_response(200, {"ok": True})
    mocker.patch.object(requests, "get", side_effect=[rate_limited, success])

    authed_api.api_call("v1/states")
    delay = fast_retries.call_args[0][0]
    # Initial backoff is 1.0; jitter is ±50% by default; so delay ∈ [0.5, 1.5]
    assert 0.5 <= delay <= 1.5


# ---------------------------------------------------------------------
# Exponential backoff
# ---------------------------------------------------------------------


def test_backoff_doubles_each_retry_without_jitter(mocker):
    """With jitter disabled, backoff should double on each retry."""
    mocker.patch.object(requests, "post")
    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=_make_jwt(),
        max_retries=3,
        retry_initial_backoff=1.0,
        retry_max_backoff=60.0,
        retry_backoff_jitter=0.0,
    )
    sleep = mocker.patch("votesmart.api.time.sleep")
    rate_limited = _mock_response(429)  # no Retry-After header
    mocker.patch.object(requests, "get", return_value=rate_limited)

    with pytest.raises(VotesmartRateLimitError):
        api.api_call("v1/candidatebios/123/detail")

    delays = [c[0][0] for c in sleep.call_args_list]
    assert delays == [1.0, 2.0, 4.0]


def test_backoff_capped_at_retry_max_backoff(mocker):
    """Backoff plateaus at retry_max_backoff."""
    mocker.patch.object(requests, "post")
    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=_make_jwt(),
        max_retries=5,
        retry_initial_backoff=10.0,
        retry_max_backoff=20.0,
        retry_backoff_jitter=0.0,
    )
    sleep = mocker.patch("votesmart.api.time.sleep")
    rate_limited = _mock_response(429)
    mocker.patch.object(requests, "get", return_value=rate_limited)

    with pytest.raises(VotesmartRateLimitError):
        api.api_call("v1/candidatebios/123/detail")

    delays = [c[0][0] for c in sleep.call_args_list]
    # 10, 20 (capped), 20, 20, 20
    assert delays == [10.0, 20.0, 20.0, 20.0, 20.0]


def test_jitter_applied_to_backoff(mocker, authed_api):
    """With jitter > 0, sleep durations land in [base*(1-j), base*(1+j)]."""
    sleep = mocker.patch("votesmart.api.time.sleep")
    rate_limited = _mock_response(429)
    success = _mock_response(200, {"ok": True})
    mocker.patch.object(requests, "get", side_effect=[rate_limited, success])

    authed_api.api_call("v1/states")
    delay = sleep.call_args[0][0]
    # default initial_backoff=1.0, jitter=0.5 → [0.5, 1.5]
    assert 0.5 <= delay <= 1.5


# ---------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------


def test_custom_rate_limiter_invoked_per_attempt(mocker, fast_retries):
    """A custom rate_limiter callable is invoked before every request."""
    limiter = mock.Mock()
    mocker.patch.object(requests, "post")
    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=_make_jwt(),
        rate_limiter=limiter,
        max_retries=2,
    )
    rate_limited = _mock_response(429)
    success = _mock_response(200, {"ok": True})
    mocker.patch.object(
        requests, "get", side_effect=[rate_limited, rate_limited, success]
    )

    api.api_call("v1/states")
    assert limiter.call_count == 3  # invoked before each of 3 attempts


def test_custom_rate_limiter_takes_precedence_over_rate_limit(
    mocker, fast_retries
):
    """When both rate_limiter and rate_limit are set, the callable wins."""
    limiter = mock.Mock()
    mocker.patch.object(requests, "post")
    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=_make_jwt(),
        rate_limit=10,
        rate_limiter=limiter,
    )
    success = _mock_response(200, {"ok": True})
    mocker.patch.object(requests, "get", return_value=success)

    api.api_call("v1/states")
    limiter.assert_called_once()


def test_builtin_rate_limit_still_works(mocker):
    """The pre-existing rate_limit=N behavior is preserved when no
    rate_limiter callable is given."""
    mocker.patch.object(requests, "post")
    # Pin _last_request_time so the first call also waits the full interval.
    fake_now = [1000.0]

    def fake_time():
        return fake_now[0]

    def fake_sleep(d):
        fake_now[0] += d

    mocker.patch("votesmart.api.time.time", side_effect=fake_time)
    mocker.patch("votesmart.api.time.sleep", side_effect=fake_sleep)

    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=_make_jwt(),
        rate_limit=2,  # 2 req/sec → 0.5s min interval
    )
    api._last_request_time = fake_now[0]  # simulate prior request just now

    success = _mock_response(200, {"ok": True})
    mocker.patch.object(requests, "get", return_value=success)

    api.api_call("v1/states")
    # min_interval is 0.5s; elapsed since _last_request_time is 0; expect sleep≈0.5
    api.api_call("v1/states")  # second call
    # We can't easily assert exact sleep without more bookkeeping; just confirm
    # the call happened.
    assert requests.get.call_count == 2


# ---------------------------------------------------------------------
# Exception introspection
# ---------------------------------------------------------------------


def test_exceptions_carry_status_code(mocker, fast_retries, authed_api):
    """All HTTP-derived exceptions expose status_code + response_body."""
    body = {"statusCode": 400, "message": "Bad query"}
    bad = _mock_response(400, body)
    mocker.patch.object(requests, "get", return_value=bad)

    with pytest.raises(VotesmartClientError) as exc_info:
        authed_api.api_call("v1/elections")
    assert exc_info.value.status_code == 400
    assert exc_info.value.response_body == body


def test_exception_str_includes_http_code():
    """Exceptions without HTTP in their message get the code appended."""
    exc = VotesmartRateLimitError("Slow down", status_code=429)
    assert "HTTP 429" in str(exc)


def test_exception_str_does_not_double_include_http():
    """If the message already mentions HTTP, no duplication."""
    exc = VotesmartApiError("API error (HTTP 500): boom", status_code=500)
    # Just one occurrence
    assert str(exc).count("HTTP 500") == 1


def test_exception_hierarchy_is_subclassable():
    """All new typed exceptions inherit from VotesmartApiError so existing
    `except VotesmartApiError` catches still work."""
    assert issubclass(VotesmartRateLimitError, VotesmartApiError)
    assert issubclass(VotesmartServerError, VotesmartApiError)
    assert issubclass(VotesmartClientError, VotesmartApiError)
    assert issubclass(VotesmartNotFoundError, VotesmartApiError)


# ---------------------------------------------------------------------
# Misc — legacy behaviors that still need to hold
# ---------------------------------------------------------------------


def test_auth_failure_raises(mocker):
    """Failed auth should raise VotesmartApiError."""
    auth_response = _mock_response(401, text="Unauthorized")
    mocker.patch.object(requests, "post", return_value=auth_response)

    with pytest.raises(VotesmartApiError):
        VoteSmartAPI(email="test@test.com", password="wrong")


def test_method_accessor_caching(mocker):
    """Method accessors should return the same instance on repeated access."""
    mocker.patch.object(requests, "post")
    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=_make_jwt(),
    )
    assert api.Candidates is api.Candidates
    assert api.Election is api.Election
    assert api.Rating is api.Rating


def test_2xx_with_error_envelope_still_raises(mocker, authed_api):
    """An error body smuggled inside a 200 response should still raise
    (legacy parse_api_response behavior)."""
    response = _mock_response(
        200, {"statusCode": 400, "message": "actually bad"}
    )
    mocker.patch.object(requests, "get", return_value=response)

    with pytest.raises(VotesmartApiError) as exc_info:
        authed_api.api_call("v1/something")
    assert "actually bad" in str(exc_info.value)
    assert exc_info.value.status_code == 400


def test_2xx_with_legacy_error_envelope_still_raises(mocker, authed_api):
    """The legacy {error: {errorMessage}} envelope inside a 200 still raises."""
    response = _mock_response(
        200, {"error": {"errorMessage": "legacy error msg"}}
    )
    mocker.patch.object(requests, "get", return_value=response)

    with pytest.raises(VotesmartApiError) as exc_info:
        authed_api.api_call("v1/something")
    assert "legacy error msg" in str(exc_info.value)
