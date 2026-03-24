from unittest import mock
from votesmart.methods.candidates import Candidates
from votesmart.methods.containers import Candidate


def test_Candidates_instantiation():
    method = Candidates(api_instance='test')
    assert method.api == 'test'


def test_getByElection_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'firstName': 'Test', 'lastName': 'User'}]}
    cands = Candidates(api)
    result = cands.getByElection(3517, stageId='G')
    api.api_call.assert_called_once_with(
        'v1/candidates/by-election', {'electionId': 3517, 'stageId': 'G', 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], Candidate)


def test_getByLastname_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'firstName': 'John', 'lastName': 'Smith'}]}
    cands = Candidates(api)
    result = cands.getByLastname('Smith', electionYear=2024)
    api.api_call.assert_called_once_with(
        'v1/candidates/by-lastname', {'lastName': 'Smith', 'electionYear': 2024, 'perPage': 1000}
    )
    assert len(result) == 1


def test_optional_params_use_is_not_none():
    """Falsy but valid values like 0 should be included."""
    api = mock.Mock()
    api.api_call.return_value = {'data': []}
    cands = Candidates(api)
    cands.getByOfficeState(officeId=3, stateId='', electionYear=0)
    call_params = api.api_call.call_args[0][1]
    assert 'stateId' in call_params
    assert 'electionYear' in call_params
