"""
Leadership methods for Vote Smart REST API 2.0.

Endpoint mapping:
    Leadership.getPositions -> GET /v1/leaderships/positions
    Leadership.getOfficials -> GET /v1/leaderships/officials
"""

from .base import APIMethodBase
from .containers import VotesmartApiObject


class LeadershipPosition(VotesmartApiObject):
    def __str__(self):
        return str(getattr(self, 'name', ''))


class LeadershipOfficial(VotesmartApiObject):
    def __str__(self):
        return '{} {}'.format(
            getattr(self, 'firstName', ''),
            getattr(self, 'lastName', ''),
        )


class Leadership(APIMethodBase):

    def getPositions(self, stateId=None, officeId=None):
        params = {}
        if stateId is not None:
            params['stateId'] = stateId
        if officeId is not None:
            params['officeId'] = officeId
        data = self.paginated_api_call('v1/leaderships/positions', params)
        return self.result_to_obj(LeadershipPosition, data)

    def getOfficials(self, leadershipId, stateId=None):
        params = {'leadershipId': leadershipId}
        if stateId is not None:
            params['stateId'] = stateId
        data = self.paginated_api_call('v1/leaderships/officials', params)
        return self.result_to_obj(LeadershipOfficial, data)
