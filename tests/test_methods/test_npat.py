from unittest import mock
from votesmart.methods.npat import Npat, NpatData


def test_Npat_instantiation():
    method = Npat(api_instance='test')
    assert method.api == 'test'


def test_getNpat_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': {'surveyMessage': 'Completed'}}
    npat = Npat(api)
    result = npat.getNpat(176111)
    api.api_call.assert_called_once_with('v1/npats/176111')
    assert isinstance(result, NpatData)
    assert str(result) == 'Completed'
