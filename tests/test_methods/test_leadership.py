from unittest import mock
from votesmart.methods.leadership import Leadership, LeadershipPosition, LeadershipOfficial


def test_Leadership_instantiation():
    method = Leadership(api_instance='test')
    assert method.api == 'test'


def test_getPositions_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'name': 'Speaker'}]}
    lead = Leadership(api)
    result = lead.getPositions(stateId='TX')
    api.api_call.assert_called_once_with(
        'v1/leaderships/positions', {'stateId': 'TX', 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], LeadershipPosition)


def test_getOfficials_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'firstName': 'John', 'lastName': 'Doe'}]}
    lead = Leadership(api)
    result = lead.getOfficials(311, stateId='TX')
    api.api_call.assert_called_once_with(
        'v1/leaderships/officials', {'leadershipId': 311, 'stateId': 'TX', 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], LeadershipOfficial)
