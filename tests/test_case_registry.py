"""Identity boundaries and no-repeat behavior on disposable synthetic records."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('case_registry', ROOT/'scripts/case_registry.py')
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)


class CaseIdentity(unittest.TestCase):
    def record(self, case_id, **kw):
        return dict(case_id=case_id, aliases=[], flags=['attempted'],
                    disposition='skip', source_fingerprints=[], sources=[], **kw)

    def test_known_id_rejected(self):
        value = {'records':[self.record('decrypt:2034')]}
        self.assertEqual(registry.check(value, 'decrypt:2034')['status'], 'REJECT')

    def test_numeric_prefix_is_not_same_case(self):
        value = {'records':[self.record('decrypt:2034')]}
        result = registry.check(value, 'decrypt:203')
        self.assertEqual(result['status'], 'CLEAR')
        self.assertFalse(result['worldwide_novelty_proven'])

    def test_shared_hash_requires_identity_review(self):
        row = self.record('synthetic:one')
        row['source_fingerprints'] = [{'kind':'sha256_file','sha256':'a'*64,'scope':'whole_source_image'}]
        self.assertEqual(registry.check({'records':[row]}, 'synthetic:two', hashes=['a'*64])['status'], 'REVIEW')

    def test_hc_url_canonicalized(self):
        self.assertEqual(registry.canonical('https://api.hcportal.eu/api/cryptograms/615'), 'hcportal:615')

    def test_public_snapshot_contains_only_allowed_metadata(self):
        seed = json.loads((ROOT/'research/NO_REPEAT_REGISTRY.json').read_text())
        self.assertGreater(len(seed['records']), 0)
        allowed = {'case_id','aliases','flags','disposition','source_fingerprints','sources'}
        for row in seed['records']:
            self.assertEqual(set(row), allowed)
            registry.validate_record(row)
            for source in row['sources']:
                self.assertEqual(set(source), {'url','evidence_type'})
                self.assertEqual(source['evidence_type'], 'PUBLIC_IDENTITY_LOCATOR_ONLY_NOT_STATUS_PROOF')


if __name__ == '__main__':
    unittest.main()
