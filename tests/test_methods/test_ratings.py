from unittest import mock
from votesmart.methods.ratings import Rating, Category, Sig, SigDetail, RatingObject


def test_Rating_instantiation():
    method = Rating(api_instance='test')
    assert method.api == 'test'


def test_getCategories_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'categoryId': 2, 'name': 'Guns'}]}
    rating = Rating(api)
    result = rating.getCategories(stateId='CA')
    api.api_call.assert_called_once_with(
        'v1/ratings/categories', {'stateId': 'CA', 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], Category)
    assert '2' in str(result[0])


def test_getSig_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': {'name': 'NRA'}}
    rating = Rating(api)
    result = rating.getSig(331)
    api.api_call.assert_called_once_with('v1/ratings/sig/331')
    assert isinstance(result, SigDetail)
    assert str(result) == 'NRA'


def test_getCandidateRating_with_sigId():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'ratingText': 'A+'}]}
    rating = Rating(api)
    result = rating.getCandidateRating(12345, sigId=331)
    api.api_call.assert_called_once_with(
        'v1/ratings/by-candidate', {'candidateId': 12345, 'sigId': 331, 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], RatingObject)
