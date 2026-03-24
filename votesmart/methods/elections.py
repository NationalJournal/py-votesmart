"""
Election methods for Vote Smart REST API 2.0.

Endpoint mapping:
    Election.getElection            -> GET /v1/elections/{id}
    Election.getElectionByYearState -> GET /v1/elections/by-year-state
    Election.getElectionByZip       -> GET /v1/elections/by-zip
    Election.getStageCandidates     -> GET /v1/elections/{id}/stage-candidates
"""

from .base import APIMethodBase
from .containers import VotesmartApiObject, Candidate, _apply_aliases


class ElectionStage(VotesmartApiObject):
    def __str__(self):
        return '%s (%s)' % (
            getattr(self, 'name', ''),
            getattr(self, 'electionDate', ''),
        )


class ElectionData(VotesmartApiObject):
    def __init__(self, d):
        # Copy to avoid mutating the caller's dict
        d = _apply_aliases(d, {'id': 'electionId', 'special': 'electionSpecial'})
        stages = d.pop('stage', None) or d.pop('stages', None)
        self.__dict__.update(d)
        if stages:
            if isinstance(stages, dict):
                self.stages = [ElectionStage(stages)]
            else:
                self.stages = [ElectionStage(s) for s in stages if s]

    def __str__(self):
        return str(getattr(self, 'name', ''))


class Election(APIMethodBase):

    def getElection(self, electionId):
        result = self.api.api_call(
            'v1/elections/{}'.format(electionId)
        )
        data = result.get('data')
        if data is None:
            data = result
        return ElectionData(data)

    def getElectionByYearState(self, year, stateId=None):
        params = {'year': year}
        if stateId is not None:
            params['stateId'] = stateId
        data = self.paginated_api_call('v1/elections/by-year-state', params)
        return self.result_to_obj(ElectionData, data)

    def getElectionByZip(self, zip5, zip4=None, year=None):
        params = {'zip5': zip5}
        if zip4 is not None:
            params['zip4'] = zip4
        if year is not None:
            params['year'] = year
        data = self.paginated_api_call('v1/elections/by-zip', params)
        return self.result_to_obj(ElectionData, data)

    def getStageCandidates(self, electionId, stageId, party=None,
                           districtId=None, stateId=None):
        params = {'stageId': stageId}
        if party is not None:
            params['party'] = party
        if districtId is not None:
            params['districtId'] = districtId
        if stateId is not None:
            params['stateId'] = stateId
        data = self.paginated_api_call(
            'v1/elections/{}/stage-candidates'.format(electionId), params
        )
        return self.result_to_obj(Candidate, data)
