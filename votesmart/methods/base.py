"""Command functions instances for API Calls
"""

from ..exceptions import VotesmartNotFoundError


class APIMethodBase:
    def __init__(self, api_instance):
        self.api = api_instance

    def result_to_obj(self, cls, result):
        "Convert a dict / list response into a list of parsed elements"
        if isinstance(result, dict):
            return [cls(result)]
        else:
            # the if o predicate is important, sometimes they return empty strings
            return [cls(o) for o in result if o]

    def paginated_api_call(self, endpoint, params=None):
        """Fetch all pages from a paginated endpoint.

        The REST API 2.0 returns paginated list responses with a 'meta'
        object containing 'currentPage', 'lastPage', and 'perPage'.
        This method fetches all pages and returns the combined data list.

        Uses perPage=1000 by default to minimize the number of requests.
        Callers can override by passing 'perPage' in params.
        """
        params = dict(params) if params else {}
        params.setdefault('perPage', 1000)
        all_data = []

        while True:
            try:
                result = self.api.api_call(endpoint, params)
            except VotesmartNotFoundError:
                # VS returns 404 ("no data" body shape) when a list-shaped
                # endpoint genuinely has nothing to return — most commonly
                # /stage-candidates for a stage that hasn't happened yet.
                # Treat as an empty list and stop paginating.
                break
            data = result.get('data', [])
            if isinstance(data, list):
                all_data.extend(data)
            else:
                # Single-item response, not paginated
                return result

            meta = result.get('meta', {})
            current_page = meta.get('currentPage', 1)
            last_page = meta.get('lastPage', 1)

            if current_page >= last_page:
                break
            params['page'] = current_page + 1

        return all_data
