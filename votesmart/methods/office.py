"""
Office methods for Vote Smart REST API 2.0.

Endpoint mapping:
    Office.getTypes              -> GET /v1/offices/types
    Office.getBranches           -> GET /v1/offices/branches
    Office.getLevels             -> GET /v1/offices/levels
    Office.getOfficesByType      -> GET /v1/offices/by-type
    Office.getOfficesByLevel     -> GET /v1/offices/by-level
    Office.getOfficesByTypeLevel -> GET /v1/offices/by-type-level
    Office.getOfficesByBranchLevel -> GET /v1/offices/by-branch-level
"""

from .base import APIMethodBase
from .containers import VotesmartApiObject


class OfficeData(VotesmartApiObject):
    def __str__(self):
        return str(getattr(self, 'name', ''))


class OfficeType(VotesmartApiObject):
    def __str__(self):
        return '{}: {}'.format(
            getattr(self, 'officeTypeId', ''),
            getattr(self, 'name', ''),
        )


class OfficeBranch(VotesmartApiObject):
    def __str__(self):
        return '{}: {}'.format(
            getattr(self, 'officeBranchId', ''),
            getattr(self, 'name', ''),
        )


class OfficeLevel(VotesmartApiObject):
    def __str__(self):
        return '{}: {}'.format(
            getattr(self, 'officeLevelId', ''),
            getattr(self, 'name', ''),
        )


class Office(APIMethodBase):

    def getTypes(self):
        data = self.paginated_api_call('v1/offices/types')
        return self.result_to_obj(OfficeType, data)

    def getBranches(self):
        data = self.paginated_api_call('v1/offices/branches')
        return self.result_to_obj(OfficeBranch, data)

    def getLevels(self):
        data = self.paginated_api_call('v1/offices/levels')
        return self.result_to_obj(OfficeLevel, data)

    def getOfficesByType(self, typeId):
        params = {'typeId': typeId}
        data = self.paginated_api_call('v1/offices/by-type', params)
        return self.result_to_obj(OfficeData, data)

    def getOfficesByLevel(self, levelId):
        params = {'levelId': levelId}
        data = self.paginated_api_call('v1/offices/by-level', params)
        return self.result_to_obj(OfficeData, data)

    def getOfficesByTypeLevel(self, officeTypeId, levelId):
        params = {'typeId': officeTypeId, 'levelId': levelId}
        data = self.paginated_api_call('v1/offices/by-type-level', params)
        return self.result_to_obj(OfficeData, data)

    def getOfficesByBranchLevel(self, branchId, levelId):
        params = {'branchId': branchId, 'levelId': levelId}
        data = self.paginated_api_call('v1/offices/by-branch-level', params)
        return self.result_to_obj(OfficeData, data)
