from unittest import mock
from votesmart.methods.officials import Officials, Official


def test_Officials_instantiation():
    method = Officials(api_instance='test')
    assert method.api == 'test'


def test_getStatewide_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {
        'data': [{'title': 'Rep.', 'firstName': 'Jane', 'lastName': 'Doe'}]
    }
    officials = Officials(api)
    result = officials.getStatewide(stateId='CA')
    api.api_call.assert_called_once_with(
        'v1/officials/by-state', {'stateId': 'CA', 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], Official)


def test_getByLastname_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'title': 'Sen.', 'firstName': 'John', 'lastName': 'Battle'}]}
    officials = Officials(api)
    result = officials.getByLastname('Battle')
    api.api_call.assert_called_once_with(
        'v1/officials/by-lastname', {'lastName': 'Battle', 'perPage': 1000}
    )
    assert len(result) == 1


def test_getByZip_with_zip4():
    api = mock.Mock()
    api.api_call.return_value = {'data': []}
    officials = Officials(api)
    officials.getByZip(90210, zip4=1234)
    api.api_call.assert_called_once_with(
        'v1/officials/by-zip', {'zip5': 90210, 'zip4': 1234, 'perPage': 1000}
    )
