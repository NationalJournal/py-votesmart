from unittest import mock
from votesmart.methods.address import Address, AddressData, WebAddress


def test_Address_instantiation():
    method = Address(api_instance='test')
    assert method.api == 'test'


def test_getCampaign_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'type': 'campaign'}]}
    addr = Address(api)
    result = addr.getCampaign(12345)
    api.api_call.assert_called_once_with(
        'v1/address/campaign/by-candidate', {'candidateId': 12345, 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], AddressData)


def test_getOfficeWebAddress_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {
        'data': [{'webAddressType': 'Website', 'webAddress': 'http://example.com'}]
    }
    addr = Address(api)
    result = addr.getOfficeWebAddress(12345)
    api.api_call.assert_called_once_with(
        'v1/address/office/web-address/by-candidate', {'candidateId': 12345, 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], WebAddress)
    assert 'Website' in str(result[0])


def test_getOfficeByOfficeState_stateId_optional():
    api = mock.Mock()
    api.api_call.return_value = {'data': []}
    addr = Address(api)
    addr.getOfficeByOfficeState(5)
    api.api_call.assert_called_once_with(
        'v1/address/office/by-office-state', {'officeId': 5, 'perPage': 1000}
    )
