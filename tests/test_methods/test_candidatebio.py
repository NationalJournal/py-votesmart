from unittest import mock
from votesmart.methods.candidatebio import (
    CandidateBio, Bio, AddlBio,
    _build_full_text, _ensure_full_text, _sort_key,
)


# --- _build_full_text tests ---

class TestBuildFullTextExperience:
    """Experience entries: political, profession, orgMembership, congMembership"""

    def test_title_and_organization(self):
        entry = {'title': 'Senator', 'organization': 'United States Senate', 'span': '2021-present', 'district': ''}
        assert _build_full_text(entry) == 'Senator, United States Senate, 2021-present'

    def test_title_org_and_district(self):
        entry = {'title': 'Representative', 'organization': 'United States House of Representatives', 'span': '2013-2015', 'district': '4'}
        assert _build_full_text(entry) == 'Representative, United States House of Representatives, District 4, 2013-2015'

    def test_title_only(self):
        entry = {'title': 'Former Member', 'organization': '', 'span': '', 'district': ''}
        assert _build_full_text(entry) == 'Former Member'

    def test_organization_only(self):
        entry = {'title': '', 'organization': 'Senate Judiciary Committee', 'span': '', 'district': ''}
        assert _build_full_text(entry) == 'Senate Judiciary Committee'

    def test_former_prefix_preserved(self):
        entry = {'title': 'Former Trustee', 'organization': 'Bridgton Academy', 'span': '', 'district': ''}
        assert _build_full_text(entry) == 'Former Trustee, Bridgton Academy'

    def test_empty_entry(self):
        entry = {'title': '', 'organization': '', 'span': '', 'district': ''}
        assert _build_full_text(entry) == ''

    def test_span_only(self):
        entry = {'title': '', 'organization': '', 'span': '2020', 'district': ''}
        assert _build_full_text(entry) == '2020'

    def test_missing_keys(self):
        entry = {}
        assert _build_full_text(entry) == ''


class TestBuildFullTextEducation:
    """Education entries: degree, field, school, span"""

    def test_full_education(self):
        entry = {'degree': 'BS', 'field': 'Foreign Service', 'school': 'Georgetown University', 'span': '2006-2009'}
        assert _build_full_text(entry) == 'BS, Foreign Service, Georgetown University, 2006-2009'

    def test_degree_and_school_no_field(self):
        entry = {'degree': 'JD', 'field': '', 'school': 'Saint Mary\'s University', 'span': '1977'}
        assert _build_full_text(entry) == 'JD, Saint Mary\'s University, 1977'

    def test_degree_only(self):
        entry = {'degree': 'MBA', 'field': '', 'school': '', 'span': ''}
        assert _build_full_text(entry) == 'MBA'

    def test_school_only(self):
        entry = {'degree': '', 'field': '', 'school': 'Harvard University', 'span': ''}
        assert _build_full_text(entry) == 'Harvard University'

    def test_school_and_span_no_degree(self):
        entry = {'degree': '', 'field': '', 'school': 'Copiah-Lincoln Community College', 'span': '1978'}
        assert _build_full_text(entry) == 'Copiah-Lincoln Community College, 1978'

    def test_degree_field_school_no_span(self):
        entry = {'degree': 'BA', 'field': 'Government', 'school': 'Saint Lawrence University', 'span': ''}
        assert _build_full_text(entry) == 'BA, Government, Saint Lawrence University'

    def test_null_field_treated_as_empty(self):
        """None values may still be present before null coercion runs"""
        entry = {'degree': 'MS', 'field': None, 'school': 'London School of Economics', 'span': '2012-2013'}
        result = _build_full_text(entry)
        assert result == 'MS, London School of Economics, 2012-2013'

    def test_education_not_confused_with_experience(self):
        """An entry with both degree/school AND title/org should use education path"""
        entry = {'degree': 'BA', 'school': 'Duke', 'title': 'Student', 'organization': 'Duke', 'span': '1975'}
        result = _build_full_text(entry)
        assert result == 'BA, Duke, 1975'

    def test_gpa_field_ignored(self):
        """gpa field exists in education entries but should not appear in fullText"""
        entry = {'degree': 'BA', 'field': 'History', 'school': 'Yale', 'span': '2000', 'gpa': '3.8'}
        result = _build_full_text(entry)
        assert result == 'BA, History, Yale, 2000'
        assert '3.8' not in result


# --- _sort_key tests ---

class TestSortKey:

    def test_newest_first(self):
        entries = [
            {'span': '2010', 'fullText': 'a'},
            {'span': '2020', 'fullText': 'b'},
            {'span': '2015', 'fullText': 'c'},
        ]
        sorted_entries = sorted(entries, key=_sort_key)
        assert [e['span'] for e in sorted_entries] == ['2020', '2015', '2010']

    def test_range_uses_start_year(self):
        entries = [
            {'span': '2005-2010', 'fullText': 'a'},
            {'span': '2015-present', 'fullText': 'b'},
            {'span': '2010-2015', 'fullText': 'c'},
        ]
        sorted_entries = sorted(entries, key=_sort_key)
        assert [e['span'] for e in sorted_entries] == ['2015-present', '2010-2015', '2005-2010']

    def test_empty_spans_sort_last(self):
        entries = [
            {'span': '', 'fullText': 'no span'},
            {'span': '2020', 'fullText': 'has span'},
        ]
        sorted_entries = sorted(entries, key=_sort_key)
        assert sorted_entries[0]['span'] == '2020'
        assert sorted_entries[1]['span'] == ''

    def test_non_numeric_span_sorts_last(self):
        entries = [
            {'span': 'present', 'fullText': 'weird'},
            {'span': '2020', 'fullText': 'normal'},
        ]
        sorted_entries = sorted(entries, key=_sort_key)
        assert sorted_entries[0]['span'] == '2020'

    def test_comma_separated_years(self):
        """Spans like "2022, 2026" should sort by the first year"""
        entries = [
            {'span': '1998', 'fullText': 'old'},
            {'span': '2022, 2026', 'fullText': 'multi'},
            {'span': '2019-present', 'fullText': 'current'},
        ]
        sorted_entries = sorted(entries, key=_sort_key)
        assert [e['span'] for e in sorted_entries] == ['2022, 2026', '2019-present', '1998']

    def test_missing_span_key(self):
        entries = [
            {'fullText': 'no span key'},
            {'span': '2020', 'fullText': 'has span'},
        ]
        sorted_entries = sorted(entries, key=_sort_key)
        assert sorted_entries[0]['span'] == '2020'


# --- _ensure_full_text tests ---

class TestEnsureFullText:

    def test_builds_fulltext_for_political(self):
        bio = {
            'political': {
                'experience': [
                    {'title': 'Senator', 'organization': 'United States Senate', 'span': '2021-present', 'district': '', 'fullText': None},
                ]
            }
        }
        result = _ensure_full_text(bio)
        assert result['political']['experience'][0]['fullText'] == 'Senator, United States Senate, 2021-present'

    def test_overwrites_existing_fulltext(self):
        """We always construct our own fullText, even if the API provided one"""
        bio = {
            'political': {
                'experience': [
                    {'title': 'Senator', 'organization': 'United States Senate', 'span': '2021-present', 'district': '', 'fullText': 'Senator, United States Senate, 2020-present'},
                ]
            }
        }
        result = _ensure_full_text(bio)
        assert result['political']['experience'][0]['fullText'] == 'Senator, United States Senate, 2021-present'

    def test_builds_fulltext_for_education(self):
        bio = {
            'education': {
                'institution': [
                    {'degree': 'BS', 'field': 'Foreign Service', 'school': 'Georgetown University', 'span': '2006-2009', 'fullText': None},
                ]
            }
        }
        result = _ensure_full_text(bio)
        assert result['education']['institution'][0]['fullText'] == 'BS, Foreign Service, Georgetown University, 2006-2009'

    def test_sorts_entries_newest_first(self):
        bio = {
            'political': {
                'experience': [
                    {'title': 'Candidate', 'organization': 'US Senate', 'span': '2017', 'district': '', 'fullText': None},
                    {'title': 'Senator', 'organization': 'US Senate', 'span': '2021-present', 'district': '', 'fullText': None},
                    {'title': 'Candidate', 'organization': 'US House', 'span': '2020', 'district': '', 'fullText': None},
                ]
            }
        }
        result = _ensure_full_text(bio)
        spans = [e['span'] for e in result['political']['experience']]
        assert spans == ['2021-present', '2020', '2017']

    def test_handles_single_entry_as_dict(self):
        """API sometimes returns a single entry as a dict instead of list"""
        bio = {
            'education': {
                'institution': {'degree': 'BA', 'field': '', 'school': 'Harvard', 'span': '1975', 'fullText': None}
            }
        }
        result = _ensure_full_text(bio)
        assert isinstance(result['education']['institution'], list)
        assert result['education']['institution'][0]['fullText'] == 'BA, Harvard, 1975'

    def test_handles_empty_sections(self):
        bio = {
            'political': {},
            'education': {'institution': []},
            'profession': {'experience': None},
        }
        result = _ensure_full_text(bio)
        assert result['political'] == {}
        assert result['education']['institution'] == []

    def test_does_not_touch_other_sections(self):
        """Sections like family, religion, offices should pass through untouched"""
        bio = {
            'family': 'Wife: Jane Doe',
            'religion': 'Catholic',
            'offices': [{'name': 'U.S. Senate'}],
            'political': {
                'experience': [
                    {'title': 'Senator', 'organization': 'US Senate', 'span': '2020', 'district': '', 'fullText': None},
                ]
            }
        }
        result = _ensure_full_text(bio)
        assert result['family'] == 'Wife: Jane Doe'
        assert result['religion'] == 'Catholic'
        assert result['offices'] == [{'name': 'U.S. Senate'}]

    def test_section_as_non_dict_skipped(self):
        """If a section value is a string or list instead of dict, skip it"""
        bio = {
            'political': 'some string value',
            'education': ['not a dict'],
        }
        result = _ensure_full_text(bio)
        assert result['political'] == 'some string value'
        assert result['education'] == ['not a dict']

    def test_handles_all_sections(self):
        bio = {
            'political': {'experience': [{'title': 'A', 'organization': 'B', 'span': '2020', 'district': '', 'fullText': None}]},
            'profession': {'experience': [{'title': 'C', 'organization': 'D', 'span': '2019', 'district': '', 'fullText': None}]},
            'education': {'institution': [{'degree': 'BA', 'field': '', 'school': 'E', 'span': '2010', 'fullText': None}]},
            'orgMembership': {'experience': [{'title': 'Member', 'organization': 'F', 'span': '', 'district': '', 'fullText': None}]},
            'congMembership': {'experience': [{'title': 'Former Chair', 'organization': 'G', 'span': '', 'district': '', 'fullText': None}]},
        }
        result = _ensure_full_text(bio)
        assert result['political']['experience'][0]['fullText'] == 'A, B, 2020'
        assert result['profession']['experience'][0]['fullText'] == 'C, D, 2019'
        assert result['education']['institution'][0]['fullText'] == 'BA, E, 2010'
        assert result['orgMembership']['experience'][0]['fullText'] == 'Member, F'
        assert result['congMembership']['experience'][0]['fullText'] == 'Former Chair, G'

    def test_skips_non_dict_entries(self):
        """Non-dict entries are left alone for fullText but sorting may reorder them"""
        bio = {
            'political': {
                'experience': [
                    'some string entry',
                    {'title': 'Senator', 'organization': 'US Senate', 'span': '2020', 'district': '', 'fullText': None},
                ]
            }
        }
        result = _ensure_full_text(bio)
        entries = result['political']['experience']
        # The dict entry gets fullText built
        dict_entry = [e for e in entries if isinstance(e, dict)][0]
        assert dict_entry['fullText'] == 'Senator, US Senate, 2020'
        # The string entry is preserved
        assert 'some string entry' in entries


# --- Bio class tests ---

class TestBio:

    def test_Bio_with_candidate_key(self):
        d = {"candidate": {"firstName": "John", "lastName": "Doe"}, "education": {"institution": []}}
        obj = Bio(d)
        assert obj.firstName == "John"

    def test_Bio_without_candidate_key(self):
        d = {"firstName": "Jane", "lastName": "Doe"}
        obj = Bio(d)
        assert obj.firstName == "Jane"

    def test_Bio_builds_fulltext_from_structured_fields(self):
        d = {
            "candidate": {
                "firstName": "Jon",
                "lastName": "Ossoff",
            },
            "education": {
                "institution": [
                    {"degree": "MS", "field": "", "school": "London School of Economics", "span": "2012-2013", "fullText": None},
                ]
            }
        }
        obj = Bio(d)
        assert obj.education['institution'][0]['fullText'] == 'MS, London School of Economics, 2012-2013'

    def test_Bio_overwrites_bad_api_fulltext(self):
        """API's fullText often has wrong dates/prefixes — we always use our own"""
        d = {
            "candidate": {"firstName": "Tom", "lastName": "Cotton"},
            "political": {
                "experience": [
                    {
                        "title": "Representative",
                        "organization": "United States House of Representatives",
                        "span": "2013-2015",
                        "district": "4",
                        "fullText": "Representative, United States House of Representatives, 2012-present",
                    },
                ]
            }
        }
        obj = Bio(d)
        # Our constructed fullText uses the correct span from structured fields
        assert obj.political['experience'][0]['fullText'] == 'Representative, United States House of Representatives, District 4, 2013-2015'

    def test_Bio_sorts_entries(self):
        d = {
            "candidate": {"firstName": "Test"},
            "political": {
                "experience": [
                    {"title": "Old", "organization": "A", "span": "2010", "district": "", "fullText": None},
                    {"title": "New", "organization": "B", "span": "2020", "district": "", "fullText": None},
                ]
            }
        }
        obj = Bio(d)
        assert obj.political['experience'][0]['span'] == '2020'
        assert obj.political['experience'][1]['span'] == '2010'


# --- Existing tests ---

def test_CandidateBio_instantiation():
    method = CandidateBio(api_instance='test')
    assert method.api == 'test'


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
