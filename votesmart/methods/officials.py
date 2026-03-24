"""
Officials methods for Vote Smart REST API 2.0.

Endpoint mapping:
    Officials.getStatewide     -> GET /v1/officials/by-state
    Officials.getByOfficeState -> GET /v1/officials/by-office-id
    Officials.getByOfficeType  -> GET /v1/officials/by-office-type
    Officials.getByLastname    -> GET /v1/officials/by-lastname
    Officials.getByLevenstein  -> GET /v1/officials/by-levenshtein
    Officials.getByDistrict    -> GET /v1/officials/by-district-id
    Officials.getByZip         -> GET /v1/officials/by-zip
"""

from .base import APIMethodBase
from .containers import VotesmartApiObject


class Official(VotesmartApiObject):
    def __str__(self):
        return '{} {} {}'.format(
            getattr(self, 'title', ''),
            getattr(self, 'firstName', ''),
            getattr(self, 'lastName', ''),
        )


class Officials(APIMethodBase):

    def getStatewide(self, stateId=None):
        params = {}
        if stateId is not None:
            params['stateId'] = stateId
        data = self.paginated_api_call('v1/officials/by-state', params)
        return self.result_to_obj(Official, data)

    def getByOfficeState(self, officeId, stateId=None):
        params = {'officeId': officeId}
        if stateId is not None:
            params['stateId'] = stateId
        data = self.paginated_api_call('v1/officials/by-office-id', params)
        return self.result_to_obj(Official, data)

    def getByOfficeType(self, officeTypeId, stateId=None):
        params = {'officeTypeId': officeTypeId}
        if stateId is not None:
            params['stateId'] = stateId
        data = self.paginated_api_call('v1/officials/by-office-type', params)
        return self.result_to_obj(Official, data)

    def getByLastname(self, lastName):
        params = {'lastName': lastName}
        data = self.paginated_api_call('v1/officials/by-lastname', params)
        return self.result_to_obj(Official, data)

    def getByLevenstein(self, lastName):
        params = {'lastName': lastName}
        data = self.paginated_api_call('v1/officials/by-levenshtein', params)
        return self.result_to_obj(Official, data)

    def getByDistrict(self, districtId):
        params = {'districtId': districtId}
        data = self.paginated_api_call('v1/officials/by-district-id', params)
        return self.result_to_obj(Official, data)

    def getByZip(self, zip5, zip4=None):
        params = {'zip5': zip5}
        if zip4 is not None:
            params['zip4'] = zip4
        data = self.paginated_api_call('v1/officials/by-zip', params)
        return self.result_to_obj(Official, data)
