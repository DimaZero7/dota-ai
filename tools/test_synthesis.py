"""Offline regression tests for the previously disconnected analyst workflow."""
import json
import tempfile
import unittest
from pathlib import Path

from src.apps.analysis.evidence import reference
from src.apps.analysis.synthesis import (
    register_measurement, prepare_analysis, accept_analysis, read_analysis, validate_analysis,
)
from src.apps.analysis.match_review import prepare_match_review


class SynthesisTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('.agent/tmp/tests'); scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve(); self.store = self.root/'store'
        self.source = self.root/'source.json'; self.source.write_text('{"kills": 12}')
        self.ref = reference(root=self.root, file=self.source, source='fixture', pointer='/kills')
        self.measure()

    def measure(self, value=12):
        register_measurement(store=self.store, node_id='facts:1', match_id=1,
            payload={'kills': value}, source_refs=[self.ref], root=self.root,
            limitations=['Kill journal differs; economy remains usable.'])

    def packet(self, level=2, children=None):
        return prepare_analysis(store=self.store, node_id=f'level:{level}', level=level,
            child_ids=children or [f'level:{level-1}' if level>2 else 'facts:1'], question='Explain behavior')

    def accept(self, packet, text='Participates while retaining resources.'):
        response = {'author':'current Codex', 'packet_id':packet['packet_id'], 'summary':text,
            'scope':'One match', 'not_established':'Visibility and intention unknown.',
            'claims':[{'statement':text, 'kind':'interpretation', 'basis':list(packet['dependencies']),
                       'why':'Outcomes coexist.', 'alternative':'Team creates the opportunity.',
                       'check':'Review another comparable interval.'}]}
        return accept_analysis(store=self.store, packet=packet, response=response)

    def test_missing_review_blocks_and_no_level_skipping(self):
        with self.assertRaisesRegex(ValueError, 'Awaiting'):
            self.packet(3)
        with self.assertRaisesRegex(ValueError, 'immediately lower'):
            self.packet(6, ['facts:1'])

    def test_parent_consumes_actual_review_not_source_totals(self):
        p = self.packet(); self.accept(p, 'Analyst explanation A')
        a = self.packet(3)
        self.assertNotIn('kills', json.dumps(a))
        self.assertIn('Analyst explanation A', json.dumps(a))
        self.accept(p, 'Revised explanation B')
        b = self.packet(3)
        self.assertNotEqual(a['packet_id'], b['packet_id'])

    def test_revision_invalidates_all_descendants(self):
        self.accept(self.packet()); self.accept(self.packet(3)); self.accept(self.packet(4))
        self.measure(11)
        with self.assertRaisesRegex(ValueError, 'Stale'):
            read_analysis(store=self.store, node_id='level:4')

    def test_bad_metric_does_not_exclude_match_and_limits_survive(self):
        for level in (2,3,4,5): self.accept(self.packet(level))
        node = read_analysis(store=self.store, node_id='level:5')
        self.assertEqual(node['match_ids'], [1])
        self.assertIn('Kill journal differs; economy remains usable.', node['limitations'])
        self.assertEqual(validate_analysis(store=self.store, node_id='level:5', root=self.root)['levels'], [1,2,3,4,5])

    def test_budget_and_source_corruption(self):
        with self.assertRaisesRegex(ValueError, 'budget'):
            prepare_analysis(store=self.store, node_id='x', level=2, child_ids=['facts:1'], question='Explain', budget_bytes=10)
        self.accept(self.packet())
        self.source.write_text('{"kills": 0}')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            validate_analysis(store=self.store, node_id='level:2', root=self.root)

    def test_profile_requires_training_priorities(self):
        for level in (2,3,4,5): self.accept(self.packet(level))
        with self.assertRaisesRegex(ValueError, 'priorities'):
            self.accept(self.packet(6))

    def test_profile_application_rejects_target_in_baseline(self):
        for level in (2,3,4,5): self.accept(self.packet(level))
        packet=self.packet(6)
        response={'packet_id':packet['packet_id'],'author':'current Codex','summary':'Working profile',
                  'scope':'Fixture','not_established':'Causality unknown.',
                  'claims':[{'statement':'Behavior','why':'Repeated','kind':'hypothesis',
                             'basis':['level:5'],'alternative':'Team context','check':'Next case'}],
                  'priorities':[{'action':'Review','reason':'Learn','baseline':'Unmeasured',
                                 'check':'Compare','basis':['level:5']}]}
        accept_analysis(store=self.store,packet=packet,response=response)
        with self.assertRaisesRegex(ValueError,'excluded'):
            prepare_match_review(store=self.store,profile_id='level:6',match_id='level:4',comparison_ids=[])


if __name__ == '__main__': unittest.main()
