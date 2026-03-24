from unittest import mock
from votesmart.methods.district import District, DistrictData


def test_District_instantiation():
    method = District(api_instance='test')
    assert method.api == 'test'


def test_getByOfficeState_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'name': 'District 1'}]}
    district = District(api)
    result = district.getByOfficeState(5, 'CA')
    api.api_call.assert_called_once_with(
        'v1/districts/by-office-state', {'officeId': 5, 'stateId': 'CA', 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], DistrictData)


def test_getByZip_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'name': 'District 5'}]}
    district = District(api)
    result = district.getByZip(90001, zip4=1234)
    api.api_call.assert_called_once_with(
        'v1/districts/by-zip', {'zip5': 90001, 'zip4': 1234, 'perPage': 1000}
    )
    assert len(result) == 1
