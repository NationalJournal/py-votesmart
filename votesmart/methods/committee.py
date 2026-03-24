"""
Committee methods for Vote Smart REST API 2.0.

Endpoint mapping:
    Committee.getTypes                -> GET /v1/committees/types
    Committee.getCommitteesByTypeState -> GET /v1/committees/by-type-state
    Committee.getCommittee            -> GET /v1/committees/{id}
    Committee.getCommitteeMembers     -> GET /v1/committees/{id}/members
"""

from .base import APIMethodBase
from .containers import VotesmartApiObject


class CommitteeType(VotesmartApiObject):
    def __str__(self):
        return str(getattr(self, 'name', ''))


class CommitteeData(VotesmartApiObject):
    def __str__(self):
        return str(getattr(self, 'name', ''))


class CommitteeDetail(VotesmartApiObject):
    def __str__(self):
        return str(getattr(self, 'name', ''))


class CommitteeMember(VotesmartApiObject):
    def __str__(self):
        return '{} {}'.format(
            getattr(self, 'firstName', ''),
            getattr(self, 'lastName', ''),
        )


class Committee(APIMethodBase):

    def getTypes(self):
        data = self.paginated_api_call('v1/committees/types')
        return self.result_to_obj(CommitteeType, data)

    def getCommitteesByTypeState(self, typeId=None, stateId=None):
        params = {}
        if typeId is not None:
            params['typeId'] = typeId
        if stateId is not None:
            params['stateId'] = stateId
        data = self.paginated_api_call('v1/committees/by-type-state', params)
        return self.result_to_obj(CommitteeData, data)

    def getCommittee(self, committeeId):
        result = self.api.api_call(
            'v1/committees/{}'.format(committeeId)
        )
        data = result.get('data')
        if data is None:
            data = result
        return CommitteeDetail(data)

    def getCommitteeMembers(self, committeeId):
        result = self.api.api_call(
            'v1/committees/{}/members'.format(committeeId)
        )
        return self.result_to_obj(CommitteeMember, result.get('data', []))
