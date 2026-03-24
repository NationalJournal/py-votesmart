"""
Address methods for Vote Smart REST API 2.0.

Endpoint mapping:
    Address.getCampaign           -> GET /v1/address/campaign/by-candidate
    Address.getCampaignWebAddress -> GET /v1/address/campaign/web-address/by-candidate
    Address.getCampaignByElection -> GET /v1/address/campaign/by-election
    Address.getOffice             -> GET /v1/address/office/by-candidate
    Address.getOfficeWebAddress   -> GET /v1/address/office/web-address/by-candidate
    Address.getOfficeByOfficeState -> GET /v1/address/office/by-office-state
"""

from .base import APIMethodBase
from .containers import VotesmartApiObject


class AddressData(VotesmartApiObject):
    def __str__(self):
        return str(getattr(self, 'type', ''))


class WebAddress(VotesmartApiObject):
    def __str__(self):
        return '{}: {}'.format(
            getattr(self, 'webAddressType', ''),
            getattr(self, 'webAddress', ''),
        )


class Address(APIMethodBase):

    def getCampaign(self, candidateId):
        params = {'candidateId': candidateId}
        data = self.paginated_api_call(
            'v1/address/campaign/by-candidate', params
        )
        return self.result_to_obj(AddressData, data)

    def getCampaignWebAddress(self, candidateId):
        params = {'candidateId': candidateId}
        data = self.paginated_api_call(
            'v1/address/campaign/web-address/by-candidate', params
        )
        return self.result_to_obj(WebAddress, data)

    def getCampaignByElection(self, electionId):
        params = {'electionId': electionId}
        data = self.paginated_api_call(
            'v1/address/campaign/by-election', params
        )
        return self.result_to_obj(AddressData, data)

    def getOffice(self, candidateId):
        params = {'candidateId': candidateId}
        data = self.paginated_api_call(
            'v1/address/office/by-candidate', params
        )
        return self.result_to_obj(AddressData, data)

    def getOfficeWebAddress(self, candidateId):
        params = {'candidateId': candidateId}
        data = self.paginated_api_call(
            'v1/address/office/web-address/by-candidate', params
        )
        return self.result_to_obj(WebAddress, data)

    def getOfficeByOfficeState(self, officeId, stateId=None):
        params = {'officeId': officeId}
        if stateId is not None:
            params['stateId'] = stateId
        data = self.paginated_api_call(
            'v1/address/office/by-office-state', params
        )
        return self.result_to_obj(AddressData, data)
