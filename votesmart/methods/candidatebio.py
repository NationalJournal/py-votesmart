"""
CandidateBio methods for Vote Smart REST API 2.0.

Endpoint mapping:
    CandidateBio.getBio        -> GET /v1/candidatebios/{id}
    CandidateBio.getDetailedBio -> GET /v1/candidatebios/{id}/detail
    CandidateBio.getAddlBio    -> GET /v1/candidatebios/{id}/addl
"""

from .base import APIMethodBase
from .containers import VotesmartApiObject, _apply_aliases


def _build_full_text(entry):
    """Construct a fullText string from structured fields when missing.

    VoteSmart's new API sometimes returns fullText as null even when the
    structured fields (title, organization, span, district) are populated.
    This reconstructs the display string to match the old API format.
    """
    parts = []
    title = entry.get('title', '')
    org = entry.get('organization', '')
    district = entry.get('district', '')
    span = entry.get('span', '')

    if title and org:
        parts.append('{}, {}'.format(title, org))
    elif org:
        parts.append(org)
    elif title:
        parts.append(title)

    if district:
        parts.append('District {}'.format(district))
    if span:
        parts.append(span)

    return ', '.join(parts)


def _ensure_full_text(bio_dict):
    """Fill in missing fullText values across all bio experience sections."""
    for section in ('political', 'profession', 'education', 'orgMembership',
                    'congMembership'):
        data = bio_dict.get(section)
        if not isinstance(data, dict):
            continue

        for key in ('experience', 'institution'):
            entries = data.get(key)
            if entries is None:
                continue
            if isinstance(entries, dict):
                entries = [entries]
            if not isinstance(entries, list):
                continue

            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                if not entry.get('fullText'):
                    built = _build_full_text(entry)
                    if built:
                        entry['fullText'] = built

            data[key] = entries

    return bio_dict


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
            merged = _ensure_full_text(merged)
            self.__dict__.update(_apply_aliases(merged, {'id': 'candidateId'}))
        else:
            d = _ensure_full_text(dict(d))
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
