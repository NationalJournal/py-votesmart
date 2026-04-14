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
    structured fields are populated. This reconstructs the display string
    to match the old API format.

    Two entry formats exist:
    - Experience entries (political, profession, orgMembership, congMembership):
      have title, organization, span, district
      e.g. "Senator, United States Senate, 2021-present"
    - Education entries: have degree, field, school, span
      e.g. "BS, Foreign Service, Georgetown University, 2006-2009"
    """
    parts = []

    # Education entries use degree/field/school
    degree = entry.get('degree', '')
    school = entry.get('school', '')
    if degree or school:
        if degree:
            parts.append(degree)
        field = entry.get('field', '')
        if field:
            parts.append(field)
        if school:
            parts.append(school)
        span = entry.get('span', '')
        if span:
            parts.append(span)
        return ', '.join(parts)

    # Experience entries use title/organization
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


def _parse_end_year(span):
    """Extract end year from a span string. 'present' counts as 9999 (newest)."""
    if not span:
        return 0
    if 'present' in span.lower():
        return 9999
    # Handle "2013-2015", "2022, 2026", "1975"
    parts = span.replace(',', ' ').split()
    # Take the last numeric token as end year
    for token in reversed(parts):
        token = token.split('-')[-1]
        try:
            return int(token)
        except ValueError:
            continue
    return 0


def _parse_start_year(span):
    """Extract start year from a span string."""
    if not span:
        return 0
    # Handle "2013-2015", "2022, 2026", "2021-present", "1975"
    first_token = span.replace(',', ' ').split()[0]
    try:
        return int(first_token.split('-')[0])
    except (ValueError, IndexError):
        return 0


def _sort_key(entry):
    """Sort key for bio entries: newest first, empty spans last.

    Sort order:
    1. End year descending ("present" is newest)
    2. Start year descending
    3. Empty spans last
    """
    span = entry.get('span', '') if isinstance(entry, dict) else ''
    if not span:
        return (1, 0, 0)  # empty spans sort last

    end_year = _parse_end_year(span)
    start_year = _parse_start_year(span)

    if not end_year and not start_year:
        return (1, 0, 0)

    return (0, -end_year, -start_year)


def _ensure_full_text(bio_dict):
    """Fill in missing fullText values and sort entries newest-first.

    The old API returned bio entries sorted by start year (newest first).
    The new API returns them in arbitrary order. This restores the expected
    sort order after filling in any missing fullText values.
    """
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
                # Always construct fullText from structured fields rather
                # than relying on the API's fullText, which often has
                # errors (wrong dates, missing prefixes, less detail).
                built = _build_full_text(entry)
                if built:
                    entry['fullText'] = built

            # Sort by start year, newest first, empty spans last
            entries.sort(key=_sort_key)
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
