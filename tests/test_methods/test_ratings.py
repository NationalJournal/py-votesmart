from unittest import mock
from votesmart.methods.ratings import Rating, Category, Sig, SigDetail, RatingObject, _filter_ratings, _extract_date_from_name


def test_Rating_instantiation():
    method = Rating(api_instance='test')
    assert method.api == 'test'


def test_getCategories_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'categoryId': 2, 'name': 'Guns'}]}
    rating = Rating(api)
    result = rating.getCategories(stateId='CA')
    api.api_call.assert_called_once_with(
        'v1/ratings/categories', {'stateId': 'CA', 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], Category)
    assert '2' in str(result[0])


def test_getSig_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': {'name': 'NRA'}}
    rating = Rating(api)
    result = rating.getSig(331)
    api.api_call.assert_called_once_with('v1/ratings/sig/331')
    assert isinstance(result, SigDetail)
    assert str(result) == 'NRA'


def test_getCandidateRating_with_sigId():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'ratingText': 'A+', 'ratingName': 'Positions'}]}
    rating = Rating(api)
    result = rating.getCandidateRating(12345, sigId=331)
    api.api_call.assert_called_once_with(
        'v1/ratings/by-candidate', {'candidateId': 12345, 'sigId': 331, 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], RatingObject)


# --- Lifetime rating filtering tests ---

class TestLifetimeRatingFiltering:

    def _make_api(self, data):
        api = mock.Mock()
        api.api_call.return_value = {'data': data}
        return api

    def test_filters_out_lifetime_positions(self):
        api = self._make_api([
            {'id': 503, 'ratingName': 'Positions [2024-10-15]', 'ratingId': 14230, 'rating': '75', 'timespan': '2023-2024'},
            {'id': 503, 'ratingName': 'Lifetime Positions [2024-10-15]', 'ratingId': 14231, 'rating': '75', 'timespan': '2023-2024'},
        ])
        result = Rating(api).getCandidateRating(57777)
        assert len(result) == 1
        assert result[0].ratingName == 'Positions [2024-10-15]'

    def test_filters_out_lifetime_scores(self):
        api = self._make_api([
            {'id': 959, 'ratingName': 'Positions', 'ratingId': 13947, 'rating': '10', 'timespan': '2023'},
            {'id': 959, 'ratingName': 'Lifetime Score', 'ratingId': 13946, 'rating': '6', 'timespan': '2023'},
        ])
        result = Rating(api).getCandidateRating(15375)
        assert len(result) == 1
        assert result[0].ratingName == 'Positions'

    def test_filters_lifetime_case_insensitive(self):
        api = self._make_api([
            {'id': 1, 'ratingName': 'Positions', 'ratingId': 100, 'rating': '50', 'timespan': '2023'},
            {'id': 1, 'ratingName': 'LIFETIME POSITIONS', 'ratingId': 101, 'rating': '50', 'timespan': '2023'},
            {'id': 1, 'ratingName': 'lifetime scores', 'ratingId': 102, 'rating': '50', 'timespan': '2023'},
        ])
        result = Rating(api).getCandidateRating(12345)
        assert len(result) == 1
        assert result[0].ratingName == 'Positions'

    def test_keeps_non_lifetime_ratings(self):
        api = self._make_api([
            {'id': 529, 'ratingName': 'Positions on Tax Rate', 'ratingId': 9620, 'rating': '48', 'timespan': '2016'},
            {'id': 529, 'ratingName': 'Positions', 'ratingId': 9618, 'rating': '57', 'timespan': '2016'},
            {'id': 529, 'ratingName': 'Positions on Spending', 'ratingId': 9619, 'rating': '52', 'timespan': '2016'},
        ])
        result = Rating(api).getCandidateRating(57777)
        assert len(result) == 3

    def test_keeps_all_when_no_lifetime(self):
        api = self._make_api([
            {'id': 1, 'ratingName': 'Positions', 'ratingId': 100, 'rating': '80', 'timespan': '2023'},
            {'id': 2, 'ratingName': 'Positions', 'ratingId': 101, 'rating': '90', 'timespan': '2023'},
        ])
        result = Rating(api).getCandidateRating(12345)
        assert len(result) == 2

    def test_empty_response(self):
        api = self._make_api([])
        result = Rating(api).getCandidateRating(12345)
        assert len(result) == 0

    def test_all_lifetime_filtered(self):
        """Edge case: if ALL ratings are Lifetime, they all get filtered"""
        api = self._make_api([
            {'id': 1, 'ratingName': 'Lifetime Positions', 'ratingId': 100, 'rating': '50', 'timespan': '2023'},
            {'id': 2, 'ratingName': 'Lifetime Scores', 'ratingId': 101, 'rating': '60', 'timespan': '2023'},
        ])
        result = Rating(api).getCandidateRating(12345)
        assert len(result) == 0

    def test_different_scores_keeps_session_rating(self):
        """When Positions and Lifetime have different scores, we keep only Positions"""
        api = self._make_api([
            {'id': 1985, 'ratingName': 'Positions [2024-10-18]', 'ratingId': 14239, 'rating': '98', 'timespan': '2023-2024'},
            {'id': 1985, 'ratingName': 'Lifetime Positions [2024-10-18]', 'ratingId': 14240, 'rating': '90', 'timespan': '2023-2024'},
        ])
        result = Rating(api).getCandidateRating(57777)
        assert len(result) == 1
        assert result[0].rating == '98'
        assert result[0].ratingId == 14239

    def test_missing_ratingName_key_kept(self):
        """Ratings without ratingName should be kept, not filtered"""
        api = self._make_api([
            {'id': 1, 'ratingId': 100, 'rating': '80', 'timespan': '2023'},
        ])
        result = Rating(api).getCandidateRating(12345)
        assert len(result) == 1

    def test_mixed_lifetime_and_subcategory_positions(self):
        """Real-world: Cato Institute has subcategory Positions + Lifetime — keep subcategories, drop Lifetime"""
        api = self._make_api([
            {'id': 529, 'ratingName': 'Positions on Tax Rate', 'ratingId': 9620, 'rating': '48', 'timespan': '2016'},
            {'id': 529, 'ratingName': 'Positions', 'ratingId': 9618, 'rating': '57', 'timespan': '2016'},
            {'id': 529, 'ratingName': 'Positions on Spending', 'ratingId': 9619, 'rating': '52', 'timespan': '2016'},
            {'id': 529, 'ratingName': 'Lifetime Positions', 'ratingId': 9621, 'rating': '55', 'timespan': '2016'},
        ])
        result = Rating(api).getCandidateRating(57777)
        assert len(result) == 3
        names = [r.ratingName for r in result]
        assert 'Lifetime Positions' not in names
        assert 'Positions on Tax Rate' in names


class TestDatedSnapshotDedup:

    def _make_api(self, data):
        api = mock.Mock()
        api.api_call.return_value = {'data': data}
        return api

    def test_keeps_most_recent_dated_snapshot(self):
        """Same SIG, same timespan, same base name — keep latest date"""
        api = self._make_api([
            {'id': 2154, 'ratingName': 'Positions [2024-02-07]', 'ratingId': 13896, 'rating': '75', 'timespan': '2023-2024'},
            {'id': 2154, 'ratingName': 'Positions [2024-07-09]', 'ratingId': 14183, 'rating': '83', 'timespan': '2023-2024'},
            {'id': 2154, 'ratingName': 'Positions [2024-10-15]', 'ratingId': 14225, 'rating': '83', 'timespan': '2023-2024'},
        ])
        result = Rating(api).getCandidateRating(57777)
        assert len(result) == 1
        assert result[0].ratingId == 14225
        assert result[0].rating == '83'

    def test_keeps_subcategory_splits(self):
        """Different base names are NOT deduped even with dates"""
        api = self._make_api([
            {'id': 529, 'ratingName': 'Positions on Tax Rate [2024-10-15]', 'ratingId': 9620, 'rating': '48', 'timespan': '2016'},
            {'id': 529, 'ratingName': 'Positions on Spending [2024-10-15]', 'ratingId': 9619, 'rating': '52', 'timespan': '2016'},
        ])
        result = Rating(api).getCandidateRating(57777)
        assert len(result) == 2

    def test_undated_entries_not_deduped(self):
        """Entries without dates in ratingName are kept as-is"""
        api = self._make_api([
            {'id': 529, 'ratingName': 'Positions on Tax Rate', 'ratingId': 9620, 'rating': '48', 'timespan': '2016'},
            {'id': 529, 'ratingName': 'Positions', 'ratingId': 9618, 'rating': '57', 'timespan': '2016'},
            {'id': 529, 'ratingName': 'Positions on Spending', 'ratingId': 9619, 'rating': '52', 'timespan': '2016'},
        ])
        result = Rating(api).getCandidateRating(57777)
        assert len(result) == 3

    def test_dated_and_undated_coexist(self):
        """An undated entry and a dated entry for the same SIG+timespan are both kept"""
        api = self._make_api([
            {'id': 1, 'ratingName': 'Positions', 'ratingId': 100, 'rating': '80', 'timespan': '2023'},
            {'id': 1, 'ratingName': 'Positions [2024-10-15]', 'ratingId': 101, 'rating': '85', 'timespan': '2023'},
        ])
        result = Rating(api).getCandidateRating(12345)
        assert len(result) == 2

    def test_combined_lifetime_and_snapshot_filtering(self):
        """Lifetime filtered first, then dated snapshots deduped"""
        api = self._make_api([
            {'id': 2154, 'ratingName': 'Positions [2024-02-07]', 'ratingId': 13896, 'rating': '75', 'timespan': '2023-2024'},
            {'id': 2154, 'ratingName': 'Positions [2024-10-15]', 'ratingId': 14225, 'rating': '83', 'timespan': '2023-2024'},
            {'id': 2154, 'ratingName': 'Lifetime Positions [2024-10-15]', 'ratingId': 14226, 'rating': '80', 'timespan': '2023-2024'},
        ])
        result = Rating(api).getCandidateRating(57777)
        assert len(result) == 1
        assert result[0].ratingId == 14225

    def test_different_sigs_same_timespan_not_deduped(self):
        """Different SIG IDs are never deduped"""
        api = self._make_api([
            {'id': 100, 'ratingName': 'Positions [2024-10-15]', 'ratingId': 1, 'rating': '80', 'timespan': '2023'},
            {'id': 200, 'ratingName': 'Positions [2024-10-15]', 'ratingId': 2, 'rating': '90', 'timespan': '2023'},
        ])
        result = Rating(api).getCandidateRating(12345)
        assert len(result) == 2


class TestExtractDateFromName:

    def test_standard_format(self):
        assert _extract_date_from_name('Positions [2024-10-15]') == '2024-10-15'

    def test_no_date(self):
        assert _extract_date_from_name('Positions') == ''

    def test_lifetime_with_date(self):
        assert _extract_date_from_name('Lifetime Positions [2024-03-05]') == '2024-03-05'

    def test_empty_string(self):
        assert _extract_date_from_name('') == ''
