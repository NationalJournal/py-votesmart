"""
CandidateBio methods for Vote Smart REST API 2.0.

Endpoint mapping:
    CandidateBio.getBio        -> GET /v1/candidatebios/{id}
    CandidateBio.getDetailedBio -> GET /v1/candidatebios/{id}/detail
    CandidateBio.getAddlBio    -> GET /v1/candidatebios/{id}/addl
"""

from .base import APIMethodBase
from .containers import VotesmartApiObject, _apply_aliases


class Bio(VotesmartApiObject):
    def __init__(self, d):
        # New API returns data at top level with 'candidate' nested,
        # or may return the candidate dict directly
        if 'candidate' in d:
            merged = dict(d['candidate'])
            # Preserve non-candidate keys (political, education, etc.)
            for key in d:
                if key != 'candidate':
                    merged[key] = d[key]
            self.__dict__.update(_apply_aliases(merged, {'id': 'candidateId'}))
        else:
            self.__dict__.update(_apply_aliases(d, {'id': 'candidateId'}))

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.__dict__)


class AddlBio(VotesmartApiObject):
    def __str__(self):
        return ': '.join((
            str(getattr(self, 'name', '')),
            str(getattr(self, 'data', '')),
        ))


class CandidateBio(APIMethodBase):
    def getBio(self, candidateId):
        result = self.api.api_call(
            'v1/candidatebios/{}'.format(candidateId)
        )
        # REST API 2.0 wraps bio in 'candidate' key, not 'data'
        if 'candidate' in result:
            return Bio(result)
        data = result.get('data')
        if data is None:
            data = result.get('bio')
        if data is None:
            data = result
        return Bio(data)

    def getDetailedBio(self, candidateId):
        result = self.api.api_call(
            'v1/candidatebios/{}/detail'.format(candidateId)
        )
        # REST API 2.0 wraps bio in 'candidate' key, not 'data'
        if 'candidate' in result:
            return Bio(result)
        data = result.get('data')
        if data is None:
            data = result.get('bio')
        if data is None:
            data = result
        return Bio(data)

    def getAddlBio(self, candidateId):
        data = self.paginated_api_call(
            'v1/candidatebios/{}/addl'.format(candidateId)
        )
        return self.result_to_obj(AddlBio, data)
