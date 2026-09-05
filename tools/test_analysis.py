"""Offline tests: python -m unittest tools.test_analysis."""
import unittest

from src.apps.analysis.schemas import Finding, inherit_limits
from src.apps.analysis.enums import Level, Support


class ContractTests(unittest.TestCase):
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
