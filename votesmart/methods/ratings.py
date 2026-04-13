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

import re

from .base import APIMethodBase
from .containers import VotesmartApiObject, _apply_aliases


def _extract_date_from_name(name):
    """Extract a date string like '2024-10-15' from a ratingName like 'Positions [2024-10-15]'."""
    match = re.search(r'\[(\d{4}-\d{2}-\d{2})\]', name)
    return match.group(1) if match else ''


def _filter_ratings(data):
    """Filter out redundant ratings from the API response.

    Two types of redundancy:
    1. "Lifetime Positions/Scores" — the new API returns both session and
       lifetime ratings as separate entries. We keep only session ratings.
    2. Dated snapshots — the same SIG may have multiple "Positions [date]"
       entries for the same timespan (updated at different times). We keep
       only the most recent snapshot.

    Subcategory splits (e.g., "Positions: Labor" vs "Positions: Budget/Tax")
    are kept because they measure different things.
    """
    # Step 1: Filter out Lifetime entries
    filtered = [
        d for d in data
        if not isinstance(d, dict)
        or 'lifetime' not in d.get('ratingName', '').lower()
    ]

    # Step 2: Dedup dated snapshots — keep most recent per SIG + timespan
    # Only dedup entries whose ratingName matches "Positions [YYYY-MM-DD]"
    # (i.e., they differ only by date, not by subcategory)
    result = []
    seen = {}  # (sig_id, timespan, base_name) -> best entry

    for d in filtered:
        if not isinstance(d, dict):
            result.append(d)
            continue

        name = d.get('ratingName', '')
        date = _extract_date_from_name(name)

        if date:
            # Strip the date portion to get the base name for grouping
            base_name = re.sub(r'\s*\[\d{4}-\d{2}-\d{2}\]\s*', '', name).strip()
            key = (d.get('id'), d.get('timespan', ''), base_name)

            if key in seen:
                existing_date = _extract_date_from_name(seen[key].get('ratingName', ''))
                if date > existing_date:
                    seen[key] = d
            else:
                seen[key] = d
        else:
            # No date in name — not a dated snapshot, keep as-is
            result.append(d)

    result.extend(seen.values())
    return result


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
        if isinstance(data, list):
            data = _filter_ratings(data)
        return self.result_to_obj(RatingObject, data)

    def getRating(self, ratingId):
        result = self.api.api_call(
            'v1/ratings/{}'.format(ratingId)
        )
        data = result.get('data')
        if data is None:
            data = result
        return VotesmartApiObject(data)
