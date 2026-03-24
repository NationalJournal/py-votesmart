"""
Candidates methods for Vote Smart REST API 2.0.

Endpoint mapping:
    Candidates.getByOfficeState     -> GET /v1/candidates/by-office-state
    Candidates.getByOfficeTypeState -> GET /v1/candidates/by-office-type-state
    Candidates.getByLastname        -> GET /v1/candidates/by-lastname
    Candidates.getByLevenstein      -> GET /v1/candidates/by-levenshtein
    Candidates.getByElection        -> GET /v1/candidates/by-election
    Candidates.getByDistrict        -> GET /v1/candidates/by-district
    Candidates.getByZip             -> GET /v1/candidates/by-zip
"""

from .base import APIMethodBase
from .containers import Candidate


class Candidates(APIMethodBase):

    def getByOfficeState(self, officeId, stateId=None, electionYear=None, stageId=None):
        params = {'officeId': officeId}
        if stateId is not None:
            params['stateId'] = stateId
        if electionYear is not None:
            params['electionYear'] = electionYear
        if stageId is not None:
            params['stageId'] = stageId
        data = self.paginated_api_call('v1/candidates/by-office-state', params)
        return self.result_to_obj(Candidate, data)

    def getByOfficeTypeState(self, officeTypeId, stateId=None, electionYear=None):
        params = {'officeTypeId': officeTypeId}
        if stateId is not None:
            params['stateId'] = stateId
        if electionYear is not None:
            params['electionYear'] = electionYear
        data = self.paginated_api_call('v1/candidates/by-office-type-state', params)
        return self.result_to_obj(Candidate, data)

    def getByLastname(self, lastName, electionYear=None):
        params = {'lastName': lastName}
        if electionYear is not None:
            params['electionYear'] = electionYear
        data = self.paginated_api_call('v1/candidates/by-lastname', params)
        return self.result_to_obj(Candidate, data)

    def getByLevenstein(self, lastName, electionYear=None):
        params = {'lastName': lastName}
        if electionYear is not None:
            params['electionYear'] = electionYear
        data = self.paginated_api_call('v1/candidates/by-levenshtein', params)
        return self.result_to_obj(Candidate, data)

    def getByElection(self, electionId, stageId=None):
        params = {'electionId': electionId}
        if stageId is not None:
            params['stageId'] = stageId
        data = self.paginated_api_call('v1/candidates/by-election', params)
        return self.result_to_obj(Candidate, data)

    def getByDistrict(self, districtId, electionYear=None):
        params = {'districtId': districtId}
        if electionYear is not None:
            params['electionYear'] = electionYear
        data = self.paginated_api_call('v1/candidates/by-district', params)
        return self.result_to_obj(Candidate, data)

    def getByZip(self, zip5, electionYear=None, zip4=None):
        params = {'zip5': zip5}
        if zip4 is not None:
            params['zip4'] = zip4
        if electionYear is not None:
            params['electionYear'] = electionYear
        data = self.paginated_api_call('v1/candidates/by-zip', params)
        return self.result_to_obj(Candidate, data)
