from unittest import mock
from votesmart.methods.measure import Measure, MeasureList, MeasureDetail


def test_Measure_instantiation():
    method = Measure(api_instance='test')
    assert method.api == 'test'


def test_getMeasuresByYearState_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': [{'title': 'Prop 1'}]}
    measure = Measure(api)
    result = measure.getMeasuresByYearState(2016, 'CA')
    api.api_call.assert_called_once_with(
        'v1/measures/by-year-state', {'year': 2016, 'stateId': 'CA', 'perPage': 1000}
    )
    assert len(result) == 1
    assert isinstance(result[0], MeasureList)


def test_getMeasure_calls_correct_endpoint():
    api = mock.Mock()
    api.api_call.return_value = {'data': {'title': 'Proposition 64'}}
    measure = Measure(api)
    result = measure.getMeasure(2142)
    api.api_call.assert_called_once_with('v1/measures/2142')
    assert isinstance(result, MeasureDetail)
    assert result.title == 'Proposition 64'
