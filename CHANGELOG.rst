py-votesmart changelog
==========================

2.1.0
-----
    * Rate-limiting / retry overhaul. ``api_call`` now transparently
      retries on transient HTTP errors (429, 502, 503, 504), honoring
      the server's ``Retry-After`` header when present and falling back
      to exponential backoff with multiplicative jitter otherwise.
      Configurable via constructor params: ``max_retries`` (default 5),
      ``retry_initial_backoff`` (1.0s), ``retry_max_backoff`` (60.0s),
      ``retry_backoff_jitter`` (±50%), ``retry_after_max`` (300.0s cap).
    * New typed exception subclasses of ``VotesmartApiError``:

        * ``VotesmartRateLimitError`` — raised on 429 after retries
          exhausted. Catch this if you want to back off further at the
          application layer.
        * ``VotesmartServerError`` — raised on 5xx after retries
          exhausted. Indicates a Vote Smart upstream problem.
        * ``VotesmartClientError`` — raised on 4xx other than 404/429
          (400/401-after-refresh/403/etc). Caller-side problem;
          retrying won't help.

      All ``VotesmartApiError`` instances (and subclasses) now carry
      ``status_code`` and ``response_body`` attributes for introspection,
      and their string form includes ``(HTTP <code>)`` automatically.
      Existing ``except VotesmartApiError`` catches still work — the
      new types subclass it.
    * New ``rate_limiter`` constructor param: pluggable callable
      ``f() -> None`` that blocks until the next request is allowed.
      Use this to plug in a distributed limiter (e.g. Redis-backed
      token bucket) shared across processes. Takes precedence over
      the existing in-process ``rate_limit=N`` (req/sec) limiter,
      which still works for the single-process case.
    * No new external dependencies.

2.0.6
-----
    * Discriminate "no data" 404s from malformed-URL 404s by inspecting the
      response body. The "no data" body shape
      (``{"message": "Not Found", "statusCode": 404}``) now raises a new
      ``VotesmartNotFoundError`` exception (a subclass of
      ``VotesmartApiError``); list-shaped endpoints that flow through
      ``paginated_api_call`` catch it and return an empty list. Express's
      "Cannot GET /v1/..." body and any other unrecognized 404 still raise
      the broad ``VotesmartApiError``. Callers previously string-matching
      ``"No candidates found"`` should switch to ``except VotesmartNotFoundError``.

0.4.5
-----
    * NationalJournal fork of ndanielsen/py-votesmart
    * Require requests>=2.20.0 (was ==2.20.0)
    * Use https for API endpoints and documentation links

0.4.4
-----
    * Add Local, Leadership, Npat, Measure and Office API methods

0.4.3
-----
    * Add Ratings method
    * Add optional param on Candidates.getByOfficeState

0.4.3
-----
    * Add Ratings method
    * Add optional param on Candidates.getByOfficeState

0.4.2
-----
    * Add additional parameter to Candidates.getByOfficeState

0.4.1
-----
    * Add requests.py to requirements.txt

0.4.0
-----
    * Major refactor of API and add test coverage from Nathan Danielsen (@ndanielsen)
    * Fix bugs and add support for several previously unsupported API methods
    * Not all API methods are implemented in new API setup

0.3.5
-----
    * Fork and restructure package from Nathan Danielsen (@ndanielsen)

0.3.4
-----
    * Python3 support from Al Johri (@AlJohri)
    * Fix getOfficesByTypeLevel from Al Johri (@AlJohri)

0.3.3
-----
    * candidate rating fix from Dan Drinkard
    * getBillsByOfficial fix from Mike Shultz

0.3.2
-----
    * workaround for bugged responses from votesmart API with blank strings

0.3.1
-----
    * some bugfixes related to changes in votesmart API

0.3.0
-----
    * new votes.getByBillNumber and officials.getStatewide methods
    * Fixed __repr__ so that eval(repr(obj)) == obj for all VotesmartApiObjects
    * zip code lookup methods (contributed by Michael Stephens)
    * fix bugs in installation and elections with a single stage (thanks slinkp)

0.2.1
-----
    * fixes to places where PVS returns single items where lists are expected
    * fix allowing fetching of BillDetail amendments (thanks Josh Eastburn)

0.2.0
-----
    * first public release (superceded unpythonic internal library)
