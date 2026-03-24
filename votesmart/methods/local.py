"""
Local methods for Vote Smart REST API 2.0.

Endpoint mapping:
    Local.getCounties  -> GET /v1/locals/counties
    Local.getCities    -> GET /v1/locals/cities
    Local.getOfficials -> GET /v1/locals/officials
"""

from .base import APIMethodBase
from .containers import VotesmartApiObject


class Locality(VotesmartApiObject):
    def __str__(self):
        return str(getattr(self, 'name', ''))


class Official(VotesmartApiObject):
    def __str__(self):
        return '{} {} {}'.format(
            getattr(self, 'title', ''),
            getattr(self, 'firstName', ''),
            getattr(self, 'lastName', ''),
        )


class Local(APIMethodBase):

    def getCounties(self, stateId):
        params = {'stateId': stateId}
        data = self.paginated_api_call('v1/locals/counties', params)
        return self.result_to_obj(Locality, data)

    def getCities(self, stateId):
        params = {'stateId': stateId}
        data = self.paginated_api_call('v1/locals/cities', params)
        return self.result_to_obj(Locality, data)

    def getOfficials(self, localId):
        params = {'localId': localId}
        data = self.paginated_api_call('v1/locals/officials', params)
        return self.result_to_obj(Official, data)
