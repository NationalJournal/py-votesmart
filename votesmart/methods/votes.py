"""
Votes methods for Vote Smart REST API 2.0.

Endpoint mapping:
    Votes.getCategories                -> GET /v1/votes/categories-by-year-state
    Votes.getBill                      -> GET /v1/votes/bills/{id}
    Votes.getBillAction                -> GET /v1/votes/bills/action/{id}
    Votes.getBillActionVotes           -> GET /v1/votes/bills/action/{id}/votes
    Votes.getBillActionVoteByOfficial  -> GET /v1/votes/bills/action/{id}/votes/by-candidate
    Votes.getByBillNumber              -> GET /v1/votes/bills/by-number
    Votes.getBillsByCategoryYearState  -> GET /v1/votes/bills/by-category-year-state
    Votes.getBillsByYearState          -> GET /v1/votes/bills/by-year-state
    Votes.getBillsByOfficialYearOffice -> GET /v1/votes/bills/by-official-year-office
    Votes.getBillsByOfficial           -> GET /v1/votes/bills/by-official
    Votes.getBillsByOfficialCategoryOffice -> GET /v1/votes/bills/by-official-category-office
    Votes.getBillsBySponsorYear        -> GET /v1/votes/bills/by-sponsor-year
    Votes.getBillsBySponsorCategory    -> GET /v1/votes/bills/by-sponsor-category
    Votes.getBillsByStateRecent        -> GET /v1/votes/bills/by-state-recent
    Votes.getVetoes                    -> GET /v1/votes/vetoes
"""

from .base import APIMethodBase
from .containers import VotesmartApiObject, _apply_aliases


class Category(VotesmartApiObject):
    def __init__(self, d):
        self.__dict__ = _apply_aliases(d, {'id': 'categoryId'})

    def __str__(self):
        return str(getattr(self, 'name', ''))


class Bill(VotesmartApiObject):
    def __init__(self, d):
        self.__dict__ = _apply_aliases(d, {'id': 'billId'})

    def __str__(self):
        return str(getattr(self, 'title', ''))


class BillDetail(VotesmartApiObject):
    def __init__(self, d):
        d = _apply_aliases(d, {'id': 'billId'})
        # Alias IDs within nested actions and categories
        actions = d.get('actions', [])
        if isinstance(actions, list):
            d['actions'] = [
                _apply_aliases(a, {'id': 'actionId'}) if isinstance(a, dict) else a
                for a in actions
            ]
        categories = d.get('categories', [])
        if isinstance(categories, list):
            d['categories'] = [
                _apply_aliases(c, {'id': 'categoryId'}) if isinstance(c, dict) else c
                for c in categories
            ]
        self.__dict__ = d

    def __str__(self):
        return str(getattr(self, 'title', ''))


class BillActionDetail(VotesmartApiObject):
    def __init__(self, d):
        self.__dict__ = _apply_aliases(d, {'id': 'actionId'})

    def __str__(self):
        return '{} - {}'.format(
            getattr(self, 'stage', ''),
            getattr(self, 'outcome', ''),
        )


class Vote(VotesmartApiObject):
    def __init__(self, d):
        self.__dict__ = _apply_aliases(d, {'id': 'candidateId'})

    def __str__(self):
        return str(getattr(self, 'action', ''))


class Veto(VotesmartApiObject):
    def __str__(self):
        return str(getattr(self, 'billNumber', ''))


class Votes(APIMethodBase):

    def getCategories(self, year, stateId=None):
        params = {'year': year}
        if stateId is not None:
            params['stateId'] = stateId
        data = self.paginated_api_call('v1/votes/categories-by-year-state', params)
        return self.result_to_obj(Category, data)

    def getBill(self, billId):
        result = self.api.api_call(
            'v1/votes/bills/{}'.format(billId)
        )
        # REST API 2.0 returns bill detail at top level, not in 'data'
        data = result.get('data')
        if data is None:
            data = result
        return BillDetail(data)

    def getBillAction(self, actionId):
        result = self.api.api_call(
            'v1/votes/bills/action/{}'.format(actionId)
        )
        # REST API 2.0 returns action detail at top level, not in 'data'
        data = result.get('data')
        if data is None:
            data = result
        return BillActionDetail(data)

    def getBillActionVotes(self, actionId):
        data = self.paginated_api_call(
            'v1/votes/bills/action/{}/votes'.format(actionId)
        )
        return self.result_to_obj(Vote, data)

    def getBillActionVoteByOfficial(self, actionId, candidateId):
        result = self.api.api_call(
            'v1/votes/bills/action/{}/votes/by-candidate'.format(actionId),
            {'candidateId': candidateId}
        )
        data = result.get('data')
        if data is None:
            data = result
        if isinstance(data, list):
            data = data[0] if data else {}
        return Vote(data)

    def getByBillNumber(self, billNumber):
        params = {'billNumber': billNumber}
        data = self.paginated_api_call('v1/votes/bills/by-number', params)
        return self.result_to_obj(Bill, data)

    def getBillsByCategoryYearState(self, categoryId, year, stateId=None):
        params = {'categoryId': categoryId, 'year': year}
        if stateId is not None:
            params['stateId'] = stateId
        data = self.paginated_api_call('v1/votes/bills/by-category-year-state', params)
        return self.result_to_obj(Bill, data)

    def getBillsByYearState(self, year, stateId=None):
        params = {'year': year}
        if stateId is not None:
            params['stateId'] = stateId
        data = self.paginated_api_call('v1/votes/bills/by-year-state', params)
        return self.result_to_obj(Bill, data)

    def getBillsByOfficialYearOffice(self, candidateId, year, officeId=None):
        params = {'candidateId': candidateId, 'year': year}
        if officeId is not None:
            params['officeId'] = officeId
        data = self.paginated_api_call('v1/votes/bills/by-official-year-office', params)
        return self.result_to_obj(Bill, data)

    def getBillsByOfficial(self, candidateId, year=None, officeId=None,
                           categoryId=None):
        params = {'candidateId': candidateId}
        if year is not None:
            params['year'] = year
        if officeId is not None:
            params['officeId'] = officeId
        if categoryId is not None:
            params['categoryId'] = categoryId
        data = self.paginated_api_call('v1/votes/bills/by-official', params)
        return self.result_to_obj(Bill, data)

    def getBillsByOfficialCategoryOffice(self, candidateId, categoryId,
                                         officeId=None):
        params = {'candidateId': candidateId, 'categoryId': categoryId}
        if officeId is not None:
            params['officeId'] = officeId
        data = self.paginated_api_call(
            'v1/votes/bills/by-official-category-office', params
        )
        return self.result_to_obj(Bill, data)

    def getBillsBySponsorYear(self, candidateId, year):
        params = {'candidateId': candidateId, 'year': year}
        data = self.paginated_api_call('v1/votes/bills/by-sponsor-year', params)
        return self.result_to_obj(Bill, data)

    def getBillsBySponsorCategory(self, candidateId, categoryId):
        params = {'candidateId': candidateId, 'categoryId': categoryId}
        data = self.paginated_api_call('v1/votes/bills/by-sponsor-category', params)
        return self.result_to_obj(Bill, data)

    def getBillsByStateRecent(self, stateId=None, amount=None):
        params = {}
        if stateId is not None:
            params['stateId'] = stateId
        if amount is not None:
            params['amount'] = amount
        data = self.paginated_api_call('v1/votes/bills/by-state-recent', params)
        return self.result_to_obj(Bill, data)

    def getVetoes(self, candidateId):
        params = {'candidateId': candidateId}
        data = self.paginated_api_call('v1/votes/vetoes', params)
        return self.result_to_obj(Veto, data)
