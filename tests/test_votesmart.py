from votesmart import VoteSmartAPI


def test_sanity():
    assert 1 + 1 == 2


def test_votesmart_api_importable():
    assert VoteSmartAPI is not None
