import pytest
from votesmart.methods import utils as uts
from votesmart.methods.containers import VotesmartApiObject


def test_sanity():
    assert 1 + 1 == 2


def test_parse_api_response():
    response = {"noerror": "here"}
    value = uts.parse_api_response(response)
    assert response == value


def test_parse_api_response_legacy_exception():
    with pytest.raises(uts.VotesmartApiError):
        response = {"error": {"errorMessage": "a message"}}
        uts.parse_api_response(response)


def test_parse_api_response_new_format_exception():
    with pytest.raises(uts.VotesmartApiError, match="Not Found"):
        response = {"statusCode": 404, "message": "Not Found"}
        uts.parse_api_response(response)


def test_parse_api_response_new_format_500():
    with pytest.raises(uts.VotesmartApiError, match="Internal Server Error"):
        response = {"statusCode": 500, "message": "Internal Server Error"}
        uts.parse_api_response(response)


def test_parse_api_response_new_format_no_error():
    """statusCode < 400 should not raise."""
    response = {"statusCode": 200, "data": []}
    value = uts.parse_api_response(response)
    assert value == response


def test_parse_api_response_non_dict():
    """Non-dict responses (e.g. lists) should pass through."""
    response = [{"id": 1}]
    value = uts.parse_api_response(response)
    assert value == response
