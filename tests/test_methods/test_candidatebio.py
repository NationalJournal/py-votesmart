from unittest import mock
from votesmart.methods.candidatebio import CandidateBio, Bio, AddlBio


def test_CandidateBio_instantiation():
    method = CandidateBio(api_instance='test')
    assert method.api == 'test'


def test_Bio_with_candidate_key():
    d = {"candidate": {"firstName": "John", "lastName": "Doe"}, "education": ["MIT"]}
    obj = Bio(d)
    assert obj.firstName == "John"
    assert obj.education == ["MIT"]


def test_Bio_without_candidate_key():
    d = {"firstName": "Jane", "lastName": "Doe"}
    obj = Bio(d)
    assert obj.firstName == "Jane"


def test_AddlBio_str():
    obj = AddlBio({"name": "Religion", "data": "Catholic"})
    assert str(obj) == "Religion: Catholic"


def test_getBio_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': {'candidate': {'firstName': 'Test'}}}
    bio = CandidateBio(api)
    result = bio.getBio(176111)
    api.api_call.assert_called_once_with('v1/candidatebios/176111')
    assert isinstance(result, Bio)


def test_getDetailedBio_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': {'firstName': 'Test'}}
    bio = CandidateBio(api)
    result = bio.getDetailedBio(176111)
    api.api_call.assert_called_once_with('v1/candidatebios/176111/detail')
    assert isinstance(result, Bio)
