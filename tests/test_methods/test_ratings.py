from unittest import mock
from votesmart.methods.ratings import Rating, Category, Sig, SigDetail, RatingObject


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
