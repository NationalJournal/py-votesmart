from unittest import mock
from votesmart.methods.committee import Committee, CommitteeType, CommitteeDetail


def test_Committee_instantiation():
    method = Committee(api_instance='test')
    assert method.api == 'test'


def test_getTypes_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'name': 'Standing'}]}
    comm = Committee(api)
    result = comm.getTypes()
    api.api_call.assert_called_once_with('v1/committees/types', {'perPage': 1000})
    assert len(result) == 1
    assert isinstance(result[0], CommitteeType)


def test_getCommittee_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': {'name': 'Finance'}}
    comm = Committee(api)
    result = comm.getCommittee(42)
    api.api_call.assert_called_once_with('v1/committees/42')
    assert isinstance(result, CommitteeDetail)
    assert result.name == 'Finance'
