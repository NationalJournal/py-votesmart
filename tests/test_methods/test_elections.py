from unittest import mock
from votesmart.methods.elections import Election, ElectionData, ElectionStage


def test_Election_instantiation():
    method = Election(api_instance='test')
    assert method.api == 'test'


def test_getElection_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': {'name': '2024 General'}}
    election = Election(api)
    result = election.getElection(3217)
    api.api_call.assert_called_once_with('v1/elections/3217')
    assert isinstance(result, ElectionData)
    assert result.name == '2024 General'


def test_getElectionByYearState_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {
        'data': [{'name': '2024 TX'}],
        'meta': {'currentPage': 1, 'lastPage': 1},
    }
    election = Election(api)
    result = election.getElectionByYearState(2024, stateId='TX')
    api.api_call.assert_called_once_with(
        'v1/elections/by-year-state',
        {'year': 2024, 'stateId': 'TX', 'perPage': 1000},
    )
    assert len(result) == 1


def test_ElectionData_parses_stages():
    data = {
        'name': '2024 General',
        'stages': [
            {'name': 'General', 'electionDate': '2024-11-05'},
            {'name': 'Primary', 'electionDate': '2024-03-05'},
        ]
    }
    ed = ElectionData(data)
    assert ed.name == '2024 General'
    assert len(ed.stages) == 2
    assert isinstance(ed.stages[0], ElectionStage)
    assert '2024-11-05' in str(ed.stages[0])


def test_ElectionData_does_not_mutate_input():
    data = {'name': 'Test', 'stages': [{'name': 'Primary'}]}
    original_keys = set(data.keys())
    ElectionData(data)
    assert set(data.keys()) == original_keys
