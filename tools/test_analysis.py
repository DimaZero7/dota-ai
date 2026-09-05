"""Offline tests: python -m unittest tools.test_analysis."""
import unittest

from src.apps.analysis.schemas import Finding, inherit_limits
from src.apps.analysis.enums import Level, Support
from src.apps.analysis.coverage import field_state
from src.apps.analysis.timebases import in_interval
from src.apps.analysis.context import ContextBudget
from src.apps.analysis.retrieval import DrillSession


class ContractTests(unittest.TestCase):
    def test_drill_stops_before_extra_fetch(self):
        session=DrillSession(max_calls=1,max_bytes=1000)
        session.request(lambda:{'events':[],'total':0},{'start':1})
        self.assertEqual(session.request(lambda:self.fail('Unexpected fetch'),{})['status'],'budget_exhausted')

    def test_budget_does_not_silently_truncate(self):
        budget=ContextBudget(total=100,answer_reserve=20,drill_reserve=20,overhead_reserve=10)
        with self.assertRaises(ValueError):
            budget.validate({'data':'я'*100})
        self.assertIsNone(budget.validate({'x':1})['measured_model_tokens'])

    def test_half_open_windows(self):
        self.assertFalse(in_interval(60,0,60))
        self.assertTrue(in_interval(60,60,120))
        self.assertTrue(in_interval(-1,-10,0))

    def test_value_states(self):
        values = {'null':None,'empty':[],'zero':0,'false':False,'value':1}
        self.assertEqual([field_state(values,k) for k in values], list(values))
        self.assertEqual(field_state({},'x'), 'missing')
        self.assertEqual(field_state({},'x',requested=False), 'not_requested')

    def test_uncertainty_and_evidence(self):
        args = dict(id='x', level=Level.MATCH, match_ids=[1], account_id=2,
                    observation='event observed', evidence=[{'source': 'test'}])
        with self.assertRaises(ValueError):
            Finding(**args, hypothesis='intent')
        with self.assertRaises(ValueError):
            Finding(**{**args,'evidence':[]})
        self.assertEqual(Finding(**args).to_dict()['support'], 'observed')
        self.assertEqual(inherit_limits([{'limitations':['visibility unknown']}]), ['visibility unknown'])


if __name__ == '__main__':
    unittest.main()
