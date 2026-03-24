from unittest import mock
from votesmart.methods.local import Local, Locality, Official


def test_Local_instantiation():
    method = Local(api_instance='test')
    assert method.api == 'test'


def test_getCounties_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'name': 'Salt Lake'}]}
    local = Local(api)
    result = local.getCounties('UT')
    api.api_call.assert_called_once_with(
        'v1/locals/counties', {'stateId': 'UT', 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], Locality)


def test_getOfficials_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {
        'data': [{'title': 'Mayor', 'firstName': 'Jane', 'lastName': 'Doe'}]
    }
    local = Local(api)
    result = local.getOfficials(4018)
    api.api_call.assert_called_once_with(
        'v1/locals/officials', {'localId': 4018, 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], Official)
