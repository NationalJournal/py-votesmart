"""
Measure methods for Vote Smart REST API 2.0.

Endpoint mapping:
    Measure.getMeasuresByYearState -> GET /v1/measures/by-year-state
    Measure.getMeasure            -> GET /v1/measures/{id}
"""

from .base import APIMethodBase
from .containers import VotesmartApiObject


class MeasureList(VotesmartApiObject):
    def __str__(self):
        return str(getattr(self, 'title', ''))


class MeasureDetail(VotesmartApiObject):
    def __str__(self):
        return str(getattr(self, 'title', ''))


class Measure(APIMethodBase):

    def getMeasuresByYearState(self, year, stateId):
        params = {'year': year, 'stateId': stateId}
        data = self.paginated_api_call('v1/measures/by-year-state', params)
        return self.result_to_obj(MeasureList, data)

    def getMeasure(self, measureId):
        result = self.api.api_call(
            'v1/measures/{}'.format(measureId)
        )
        data = result.get('data')
        if data is None:
            data = result
        return MeasureDetail(data)
