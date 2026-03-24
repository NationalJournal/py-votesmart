"""
NPAT (Political Courage Test) methods for Vote Smart REST API 2.0.

Endpoint mapping:
    Npat.getNpat -> GET /v1/npats/{id}
"""

from .base import APIMethodBase
from .containers import VotesmartApiObject


class NpatData(VotesmartApiObject):
    def __str__(self):
        return str(getattr(self, 'surveyMessage', ''))


class Npat(APIMethodBase):

    def getNpat(self, candidateId):
        result = self.api.api_call(
            'v1/npats/{}'.format(candidateId)
        )
        data = result.get('data')
        if data is None:
            data = result
        return NpatData(data)
