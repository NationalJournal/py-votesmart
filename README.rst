
================
py-votesmart
================

Python 3 supported library for interacting with the Project Vote Smart API.

The Project Vote Smart API provides detailed information on politicians,
including bios, votes, and NPAT responses.
(https://votesmart.org/share/api)

All code is under a BSD-style license, see LICENSE for details.

================
Backstory
================
py-votesmart is a fork of the python-votesmart which is a project of Sunlight Labs (c) 2008.
Originally written by James Turk <jturk@sunlightfoundation.com>.

Original Source: https://github.com/votesmart/python-votesmart

Python 3 fork: https://github.com/ndanielsen/py-votesmart

Installation
============
py-votesmart is compatible with Python 2.7 or later, but it is preferred to use Python 3.5 or later to take full advantage of all functionality.

Usage
=====

To initialize the api, all that is required is for it to be imported and for an
API key to be defined.

(If you do not have an API key visit https://votesmart.org/share/api to
register for one.)

Import ``votesmart`` from ``VoteSmartAPI``:

    >>> from votesmart import VoteSmartAPI

And set your API key:

    >>> vsmart = VoteSmartAPI(api_key="VOTE_SMART_API_KEY")

