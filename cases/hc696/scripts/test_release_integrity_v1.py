"""Meaningful negative checks in disposable copies; never edit sealed evidence."""
from pathlib import Path
import json,shutil,tempfile,unittest
import verify_solution_v1 as checker
class ReleaseIntegrity(unittest.TestCase):
    def setUp(self):
        self.saved=checker.ROOT;self.tmp=tempfile.TemporaryDirectory()
        checker.ROOT=Path(self.tmp.name)
        for name in ['config/TARGET_SOURCE_REGISTRATION_v1.json',
            'reports/independent_source_review_v1/source_ledger_v1.json',
            'reports/independent_source_review_v1/freeze_manifest_v1.json',
            'experiments/target_first_v1/CANDIDATE_v1.json',
            'experiments/target_first_v1/SEARCH_RESULTS_v1.tsv',
            'reports/root_forward_certificate_v1/CERTIFICATE_v1.json']:
            to=checker.ROOT/name;to.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(self.saved/name,to)
    def tearDown(self):checker.ROOT=self.saved;self.tmp.cleanup()
    def change(self,name,fn):
        p=checker.ROOT/name;d=json.loads(p.read_text());fn(d);p.write_text(json.dumps(d))
    def test_original(self):self.assertEqual(checker.verify()['observed_positions'],180)
    def test_plaintext_edit_rejected(self):
        self.change('experiments/target_first_v1/CANDIDATE_v1.json',lambda d:d['best'].__setitem__('plaintext','N'+d['best']['plaintext'][1:]))
        with self.assertRaises(AssertionError):checker.verify()
    def test_slide_edit_rejected(self):
        self.change('experiments/target_first_v1/CANDIDATE_v1.json',lambda d:d['effective_slides'].__setitem__(0,8))
        with self.assertRaises(AssertionError):checker.verify()
    def test_source_edit_rejected(self):
        self.change('reports/independent_source_review_v1/source_ledger_v1.json',lambda d:d['occurrences'][0].__setitem__('visible_final_uppercase','D'))
        with self.assertRaises(AssertionError):checker.verify()
    def test_wrong_pair_provenance_rejected(self):
        self.change('reports/root_forward_certificate_v1/CERTIFICATE_v1.json',lambda d:d[0].__setitem__('paired_source_index',8))
        with self.assertRaises(AssertionError):checker.verify()
    def test_typed_underlayer_hold_removal_rejected(self):
        self.change('config/TARGET_SOURCE_REGISTRATION_v1.json',lambda d:d.__setitem__('typed_underlayer_held_positions',[]))
        with self.assertRaises(AssertionError):checker.verify()
if __name__=='__main__':unittest.main()
