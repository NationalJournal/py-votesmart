"""
State methods for Vote Smart REST API 2.0.

Endpoint mapping:
    State.getStateIDs -> GET /v1/states
    State.getState    -> GET /v1/states/{id}
"""

from .base import APIMethodBase
from .containers import VotesmartApiObject


class StateData(VotesmartApiObject):
    def __str__(self):
        return '{} {}'.format(
            getattr(self, 'stateId', ''),
            getattr(self, 'name', ''),
        )


class StateDetail(VotesmartApiObject):
    def __str__(self):
        return '{} {}'.format(
            getattr(self, 'stateId', ''),
            getattr(self, 'name', ''),
        )


class State(APIMethodBase):

    def getStateIDs(self):
        data = self.paginated_api_call('v1/states')
        return self.result_to_obj(StateData, data)

    def getState(self, stateId):
        result = self.api.api_call(
            'v1/states/{}'.format(stateId)
        )
        data = result.get('data')
        if data is None:
            data = result
        return StateDetail(data)
