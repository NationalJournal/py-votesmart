"""
Rating methods for Vote Smart REST API 2.0.

Endpoint mapping:
    Rating.getCategories       -> GET /v1/ratings/categories
    Rating.getSigList          -> GET /v1/ratings/siglist
    Rating.getSig              -> GET /v1/ratings/sig/{id}
    Rating.getSigRatings       -> GET /v1/ratings/sig/{id}/ratings
    Rating.getCandidateRating  -> GET /v1/ratings/by-candidate
    Rating.getRating           -> GET /v1/ratings/{id}
"""

from .base import APIMethodBase
from .containers import VotesmartApiObject, _apply_aliases


class Category(VotesmartApiObject):
    def __init__(self, d):
        self.__dict__ = _apply_aliases(d, {'id': 'categoryId'})

    def __str__(self):
        return ': '.join((
            str(getattr(self, 'categoryId', '')),
            str(getattr(self, 'name', '')),
        ))


class Sig(VotesmartApiObject):
    def __init__(self, d):
        self.__dict__ = _apply_aliases(d, {'id': 'sigId'})

    def __str__(self):
        return ': '.join((
            str(getattr(self, 'sigId', '')),
            str(getattr(self, 'name', '')),
        ))


class SigDetail(VotesmartApiObject):
    def __init__(self, d):
        self.__dict__ = _apply_aliases(d, {'id': 'sigId'})

    def __str__(self):
        return str(getattr(self, 'name', ''))


class RatingObject(VotesmartApiObject):
    def __init__(self, d):
        self.__dict__ = _apply_aliases(d, {'id': 'sigId'})

    def __str__(self):
        return str(getattr(self, 'ratingText', ''))


class Rating(APIMethodBase):

    def getCategories(self, stateId=None):
        params = {}
        if stateId is not None:
            params['stateId'] = stateId
        data = self.paginated_api_call('v1/ratings/categories', params)
        return self.result_to_obj(Category, data)

    def getSigList(self, categoryId, stateId=None):
        params = {'categoryId': categoryId}
        if stateId is not None:
            params['stateId'] = stateId
        data = self.paginated_api_call('v1/ratings/siglist', params)
        return self.result_to_obj(Sig, data)

    def getSig(self, sigId):
        result = self.api.api_call(
            'v1/ratings/sig/{}'.format(sigId)
        )
        # REST API 2.0 returns sig detail at top level, not in 'data'
        data = result.get('data')
        if data is None:
            data = result
        return SigDetail(data)

    def getSigRatings(self, sigId):
        data = self.paginated_api_call(
            'v1/ratings/sig/{}/ratings'.format(sigId)
        )
        return self.result_to_obj(VotesmartApiObject, data)

    def getCandidateRating(self, candidateId, sigId=None):
        params = {'candidateId': candidateId}
        if sigId is not None:
            params['sigId'] = sigId
        data = self.paginated_api_call('v1/ratings/by-candidate', params)
        # The new API returns both "Positions" and "Lifetime Positions"
        # ratings as separate entries for the same SIG and timespan.
        # The old API only returned session ratings. Filter out Lifetime
        # entries to avoid near-duplicates.
        if isinstance(data, list):
            data = [
                d for d in data
                if not isinstance(d, dict)
                or 'lifetime' not in d.get('ratingName', '').lower()
            ]
        return self.result_to_obj(RatingObject, data)

    def getRating(self, ratingId):
        result = self.api.api_call(
            'v1/ratings/{}'.format(ratingId)
        )
        data = result.get('data')
        if data is None:
            data = result
        return VotesmartApiObject(data)
