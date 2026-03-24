from votesmart.methods.containers import VotesmartApiObject
from votesmart.methods.base import APIMethodBase


def test_result_to_obj_dict():
    data = {'address': '123 address', 'phone': ['623-232-2321']}
    obj = APIMethodBase(api_instance="fake instance")
    result = obj.result_to_obj(VotesmartApiObject, data)
    assert len(result) == 1
    assert result[0].address == '123 address'


def test_result_to_obj_list():
    data = [{'name': 'Alice'}, {'name': 'Bob'}]
    obj = APIMethodBase(api_instance="fake instance")
    result = obj.result_to_obj(VotesmartApiObject, data)
    assert len(result) == 2
    assert result[0].name == 'Alice'
    assert result[1].name == 'Bob'


def test_result_to_obj_filters_empty_strings():
    data = [{'name': 'Alice'}, '', {'name': 'Bob'}, '']
    obj = APIMethodBase(api_instance="fake instance")
    result = obj.result_to_obj(VotesmartApiObject, data)
    assert len(result) == 2


def test_result_to_obj_empty_list():
    obj = APIMethodBase(api_instance="fake instance")
    result = obj.result_to_obj(VotesmartApiObject, [])
    assert result == []
