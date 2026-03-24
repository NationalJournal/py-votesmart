"""
District methods for Vote Smart REST API 2.0.

Endpoint mapping:
    District.getByOfficeState -> GET /v1/districts/by-office-state
    District.getByZip         -> GET /v1/districts/by-zip
"""

from .base import APIMethodBase
from .containers import VotesmartApiObject


class DistrictData(VotesmartApiObject):
    def __str__(self):
        return str(getattr(self, 'name', ''))


class District(APIMethodBase):

    def getByOfficeState(self, officeId, stateId, districtName=None):
        params = {'officeId': officeId, 'stateId': stateId}
        if districtName is not None:
            params['districtName'] = districtName
        data = self.paginated_api_call('v1/districts/by-office-state', params)
        return self.result_to_obj(DistrictData, data)

    def getByZip(self, zip5, zip4=None):
        params = {'zip5': zip5}
        if zip4 is not None:
            params['zip4'] = zip4
        data = self.paginated_api_call('v1/districts/by-zip', params)
        return self.result_to_obj(DistrictData, data)
