import json
import time
import base64
from unittest import mock

import requests
import pytest

from votesmart.api import VoteSmartAPI
from votesmart.exceptions import VotesmartApiError, VotesmartNotFoundError


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
    mocker.patch.object(requests, 'post')
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

    auth_response = mock.Mock()
    auth_response.status_code = 200
    auth_response.json.return_value = {"accessToken": new_token}
    mocker.patch.object(requests, 'post', return_value=auth_response)

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
    auth_response = mock.Mock()
    auth_response.status_code = 200
    auth_response.json.return_value = {"accessToken": new_token}
    mocker.patch.object(requests, 'post', return_value=auth_response)

    api = VoteSmartAPI(email="test@test.com", password="password")
    requests.post.assert_called_once()
    assert api.access_token == new_token


def test_api_call(mocker):
    """api_call should make a GET with Bearer auth header."""
    token = _make_jwt()
    mocker.patch.object(requests, 'post')

    json_mock = mock.Mock()
    json_mock.status_code = 200
    json_mock.json.return_value = {'data': [{'id': 1}]}
    mocker.patch.object(requests, 'get', return_value=json_mock)

    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=token,
    )
    response = api.api_call('v1/elections/by-year-state', {'year': 2024})

    requests.get.assert_called_once()
    call_args = requests.get.call_args
    assert 'v1/elections/by-year-state' in call_args[0][0]
    assert 'Bearer' in call_args[1]['headers']['Authorization']
    assert response == {'data': [{'id': 1}]}


def test_api_call_retries_on_401(mocker):
    """On 401, api_call should re-authenticate and retry."""
    token = _make_jwt()
    new_token = _make_jwt(exp=int(time.time()) + 90000)

    auth_response = mock.Mock()
    auth_response.status_code = 200
    auth_response.json.return_value = {"accessToken": new_token}
    mocker.patch.object(requests, 'post', return_value=auth_response)

    unauthorized = mock.Mock()
    unauthorized.status_code = 401
    success = mock.Mock()
    success.status_code = 200
    success.json.return_value = {'data': []}
    mocker.patch.object(requests, 'get', side_effect=[unauthorized, success])

    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=token,
    )
    response = api.api_call('v1/states')
    assert requests.get.call_count == 2
    assert response == {'data': []}


def test_api_call_raises_endpoint_not_found_on_malformed_url_404(mocker):
    """404 with Express's "Cannot GET" body shape signals a wrong URL — a
    caller bug. Always raises the broad VotesmartApiError (not the subclass)
    so the data-not-found path stays distinguishable."""
    token = _make_jwt()
    mocker.patch.object(requests, 'post')

    not_found = mock.Mock()
    not_found.status_code = 404
    not_found.json.return_value = {
        "message": "Cannot GET /v1/nonexistent",
        "error": "Not Found",
        "statusCode": 404,
    }
    mocker.patch.object(requests, 'get', return_value=not_found)

    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=token,
    )
    with pytest.raises(VotesmartApiError) as exc_info:
        api.api_call('v1/nonexistent')
    # Should be the broad type, not the data-not-found subclass.
    assert not isinstance(exc_info.value, VotesmartNotFoundError)
    assert "Endpoint not found" in str(exc_info.value)


def test_api_call_raises_not_found_subclass_on_data_not_found_404(mocker):
    """404 with the "no data" body shape signals the route is valid but VS
    has nothing for this query (e.g. a General stage before the Primary has
    happened). Raises VotesmartNotFoundError so list-shaped callers can
    catch and treat as empty."""
    token = _make_jwt()
    mocker.patch.object(requests, 'post')

    not_found = mock.Mock()
    not_found.status_code = 404
    not_found.json.return_value = {"message": "Not Found", "statusCode": 404}
    mocker.patch.object(requests, 'get', return_value=not_found)

    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=token,
    )
    with pytest.raises(VotesmartNotFoundError) as exc_info:
        api.api_call('v1/elections/5342/stage-candidates', {'stageId': 'G'})
    assert "Resource not found" in str(exc_info.value)


def test_api_call_raises_endpoint_not_found_on_unparseable_404_body(mocker):
    """If the 404 body isn't JSON (HTML error page from a load balancer,
    empty body, etc.) treat it as an unknown error and raise the broad
    type. Only the explicit "no data" body shape opts in to the typed
    subclass — anything else stays visible."""
    token = _make_jwt()
    mocker.patch.object(requests, 'post')

    not_found = mock.Mock()
    not_found.status_code = 404
    not_found.json.side_effect = ValueError("No JSON")
    mocker.patch.object(requests, 'get', return_value=not_found)

    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=token,
    )
    with pytest.raises(VotesmartApiError) as exc_info:
        api.api_call('v1/something')
    assert not isinstance(exc_info.value, VotesmartNotFoundError)


def test_api_call_raises_on_500_with_json(mocker):
    """500 with JSON body should raise via parse_api_response."""
    token = _make_jwt()
    mocker.patch.object(requests, 'post')

    error_response = mock.Mock()
    error_response.status_code = 500
    error_response.json.return_value = {
        "statusCode": 500, "message": "Internal Server Error"
    }
    mocker.patch.object(requests, 'get', return_value=error_response)

    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=token,
    )
    with pytest.raises(VotesmartApiError, match="Internal Server Error"):
        api.api_call('v1/states')


def test_api_call_raises_on_500_without_json(mocker):
    """500 with non-JSON body should include status code in error."""
    token = _make_jwt()
    mocker.patch.object(requests, 'post')

    error_response = mock.Mock()
    error_response.status_code = 500
    error_response.json.side_effect = ValueError("No JSON")
    error_response.text = "<html>Internal Server Error</html>"
    mocker.patch.object(requests, 'get', return_value=error_response)

    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=token,
    )
    with pytest.raises(VotesmartApiError, match="HTTP 500"):
        api.api_call('v1/states')


def test_auth_failure_raises(mocker):
    """Failed auth should raise VotesmartApiError."""
    auth_response = mock.Mock()
    auth_response.status_code = 401
    auth_response.text = "Unauthorized"
    mocker.patch.object(requests, 'post', return_value=auth_response)

    with pytest.raises(VotesmartApiError):
        VoteSmartAPI(email="test@test.com", password="wrong")


def test_method_accessor_caching(mocker):
    """Method accessors should return the same instance on repeated access."""
    token = _make_jwt()
    mocker.patch.object(requests, 'post')

    api = VoteSmartAPI(
        email="test@test.com",
        password="password",
        access_token=token,
    )
    assert api.Candidates is api.Candidates
    assert api.Election is api.Election
    assert api.Rating is api.Rating
