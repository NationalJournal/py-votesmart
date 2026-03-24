from unittest import mock
from votesmart.methods.states import State, StateData, StateDetail


def test_State_instantiation():
    method = State(api_instance='test')
    assert method.api == 'test'


def test_getStateIDs_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'stateId': 'TX', 'name': 'Texas'}]}
    state = State(api)
    result = state.getStateIDs()
    api.api_call.assert_called_once_with('v1/states', {'perPage': 1000})
    assert len(result) == 1
    assert isinstance(result[0], StateData)
    assert 'TX' in str(result[0])


def test_getState_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': {'stateId': 'TX', 'name': 'Texas'}}
    state = State(api)
    result = state.getState('TX')
    api.api_call.assert_called_once_with('v1/states/TX')
    assert isinstance(result, StateDetail)
    assert result.name == 'Texas'
