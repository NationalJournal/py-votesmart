from unittest import mock
from votesmart.methods.office import Office, OfficeType, OfficeData


def test_Office_instantiation():
    method = Office(api_instance='test')
    assert method.api == 'test'


def test_getTypes_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'officeTypeId': 'C', 'name': 'Congressional'}]}
    office = Office(api)
    result = office.getTypes()
    api.api_call.assert_called_once_with('v1/offices/types', {'perPage': 1000})
    assert len(result) == 1
    assert isinstance(result[0], OfficeType)
    assert 'Congressional' in str(result[0])


def test_getOfficesByTypeLevel_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'name': 'US Senate'}]}
    office = Office(api)
    result = office.getOfficesByTypeLevel('C', 'F')
    api.api_call.assert_called_once_with(
        'v1/offices/by-type-level', {'typeId': 'C', 'levelId': 'F', 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], OfficeData)
