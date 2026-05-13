from unittest import mock

from votesmart.exceptions import VotesmartNotFoundError
from votesmart.methods.containers import VotesmartApiObject
from votesmart.methods.base import APIMethodBase


def test_result_to_obj_dict():
    data = {'address': '123 address', 'phone': ['623-232-2321']}
    obj = APIMethodBase(api_instance="fake instance")
    result = obj.result_to_obj(VotesmartApiObject, data)
    assert len(result) == 1
    assert result[0].address == '123 address'


def test_result_to_obj_list():
    data = [{'name': 'Alice'}, {'name': 'Bob'}]
    obj = APIMethodBase(api_instance="fake instance")
    result = obj.result_to_obj(VotesmartApiObject, data)
    assert len(result) == 2
    assert result[0].name == 'Alice'
    assert result[1].name == 'Bob'


def test_result_to_obj_filters_empty_strings():
    data = [{'name': 'Alice'}, '', {'name': 'Bob'}, '']
    obj = APIMethodBase(api_instance="fake instance")
    result = obj.result_to_obj(VotesmartApiObject, data)
    assert len(result) == 2


def test_result_to_obj_empty_list():
    obj = APIMethodBase(api_instance="fake instance")
    result = obj.result_to_obj(VotesmartApiObject, [])
    assert result == []


def test_paginated_api_call_returns_empty_on_not_found():
    """List-shaped endpoints surface VS's "no data" 404 as an empty list,
    so the caller can iterate normally without an exception. Common case:
    /stage-candidates for a stage VS doesn't have candidates for yet."""
    fake_api = mock.Mock()
    fake_api.api_call.side_effect = VotesmartNotFoundError(
        "Resource not found: v1/elections/5342/stage-candidates (HTTP 404)"
    )
    obj = APIMethodBase(api_instance=fake_api)
    result = obj.paginated_api_call(
        'v1/elections/5342/stage-candidates', {'stageId': 'G'}
    )
    assert result == []
    fake_api.api_call.assert_called_once()


def test_paginated_api_call_stops_paginating_on_not_found_mid_stream():
    """If a subsequent page comes back as 404 (unusual but possible), stop
    paginating and return whatever was collected up to that point."""
    page_one = {
        'data': [{'id': 1}],
        'meta': {'currentPage': 1, 'lastPage': 2, 'perPage': 1000},
    }
    fake_api = mock.Mock()
    fake_api.api_call.side_effect = [
        page_one,
        VotesmartNotFoundError("Resource not found (HTTP 404)"),
    ]
    obj = APIMethodBase(api_instance=fake_api)
    result = obj.paginated_api_call('v1/something')
    assert result == [{'id': 1}]
    assert fake_api.api_call.call_count == 2
