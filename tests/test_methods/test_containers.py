from votesmart.methods.containers import VotesmartApiObject, Candidate


def test_sanity():
    assert 1 + 1 == 2


def test_VotesmartApiObject():
    data = {"hello": "friend"}
    result = VotesmartApiObject(data)
    assert result.hello == "friend"


def test_VotesmartApiObject_get_default_is_none():
    data = {"hello": "friend"}
    result = VotesmartApiObject(data)
    assert result.get("missing") is None


def test_VotesmartApiObject_get_with_default():
    data = {"hello": "friend"}
    result = VotesmartApiObject(data)
    assert result.get("missing", "fallback") == "fallback"


def test_VotesmartApiObject_contains():
    data = {"hello": "friend"}
    result = VotesmartApiObject(data)
    assert "hello" in result
    assert "missing" not in result


def test_VotesmartApiObject_eq():
    data = {"hello": "friend"}
    a = VotesmartApiObject(dict(data))
    b = VotesmartApiObject(dict(data))
    assert a == b


def test_VotesmartApiObject_eq_dict():
    data = {"hello": "friend"}
    result = VotesmartApiObject(data)
    assert result == {"hello": "friend"}


def test_VotesmartApiObject_len():
    data = {"a": 1, "b": 2}
    result = VotesmartApiObject(data)
    assert len(result) == 2


def test_Candidate_str():
    data = {"firstName": "John", "lastName": "Doe"}
    c = Candidate(data)
    assert str(c) == "John Doe"


def test_Candidate_get_inherits_from_parent():
    data = {"firstName": "John"}
    c = Candidate(data)
    assert c.get("missing") is None
    assert c.get("firstName") == "John"
