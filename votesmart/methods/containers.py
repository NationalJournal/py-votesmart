"""Containers to hold individual data items in a response
"""


def _apply_aliases(d, aliases):
    """Return a copy of d with legacy field names added as aliases.

    For example, if aliases={'id': 'candidateId'} and d has 'id' but not
    'candidateId', the returned dict will have both 'id' and 'candidateId'.

    Always returns a new dict to avoid mutating the caller's data.
    """
    d = dict(d)
    for new_name, old_name in aliases.items():
        if new_name in d and old_name not in d:
            d[old_name] = d[new_name]
    return d


class VotesmartApiObject(dict):
    "Dictionary like object"

    def __init__(self, d):
        self.__dict__ = d

    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def __getitem__(self, key):
        return self.__dict__[key]

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __delitem__(self, key):
        del self.__dict__[key]

    def __eq__(self, other):
        if isinstance(other, dict):
            return self.__dict__ == other
        if isinstance(other, VotesmartApiObject):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __contains__(self, item):
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)

    def clear(self):
        return self.__dict__.clear()

    def copy(self):
        return self.__dict__.copy()

    def get(self, k, default=None):
        if k in self.__dict__:
            return self.__dict__[k]
        return default

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def pop(self, *args):
        return self.__dict__.pop(*args)


class Candidate(VotesmartApiObject):
    def __init__(self, d):
        self.__dict__ = _apply_aliases(d, {'id': 'candidateId'})

    def __str__(self):
        return ' '.join((
            getattr(self, 'firstName', ''),
            getattr(self, 'lastName', ''),
        ))
