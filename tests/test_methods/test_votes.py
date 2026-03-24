from unittest import mock
from votesmart.methods.votes import Votes, Bill, BillDetail, Vote


def test_Votes_instantiation():
    method = Votes(api_instance='test')
    assert method.api == 'test'


def test_getByBillNumber_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'title': 'HB 1'}]}
    votes = Votes(api)
    result = votes.getByBillNumber('HB 1')
    api.api_call.assert_called_once_with(
        'v1/votes/bills/by-number', {'billNumber': 'HB 1', 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], Bill)


def test_getBill_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': {'title': 'Test Bill'}}
    votes = Votes(api)
    result = votes.getBill(999)
    api.api_call.assert_called_once_with('v1/votes/bills/999')
    assert isinstance(result, BillDetail)
    assert result.title == 'Test Bill'


def test_getBillActionVotes_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'action': 'Yea'}]}
    votes = Votes(api)
    result = votes.getBillActionVotes(100)
    api.api_call.assert_called_once_with('v1/votes/bills/action/100/votes', {'perPage': 1000})
    assert len(result) == 1
    assert isinstance(result[0], Vote)


def test_getBillsByStateRecent_includes_amount():
    api = mock.Mock()
    api.api_call.return_value = {'data': []}
    votes = Votes(api)
    votes.getBillsByStateRecent(stateId='CA', amount=10)
    api.api_call.assert_called_once_with(
        'v1/votes/bills/by-state-recent', {'stateId': 'CA', 'amount': 10, 'perPage': 1000}
    )


def test_getCategories_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'name': 'Budget'}]}
    votes = Votes(api)
    result = votes.getCategories(2024, stateId='TX')
    api.api_call.assert_called_once_with(
        'v1/votes/categories-by-year-state', {'year': 2024, 'stateId': 'TX', 'perPage': 1000}
    )
    assert len(result) == 1
