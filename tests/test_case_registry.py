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

    def test_parent_alias_blocks_new_attack_without_merging(self):
        row = self.record('archive-item:synthetic-letter')
        row['aliases'] = ['cyphersolver:342']
        result = registry.check({'records':[row]}, 'cyphersolver:342')
        self.assertEqual(result['status'], 'REVIEW')
        self.assertEqual(result['resource_alias_matches'], [row['case_id']])
        self.assertEqual(result['identity_matches'], [])

    def test_parent_alias_numeric_prefix_does_not_collide(self):
        row = self.record('archive-item:synthetic-letter')
        row['aliases'] = ['cyphersolver:342']
        self.assertEqual(registry.check({'records':[row]}, 'cyphersolver:34')['status'], 'CLEAR')

    def test_related_child_id_is_checked_in_its_own_namespace(self):
        row = self.record('decrypt:392')
        value = {'records':[row]}
        self.assertEqual(registry.check(value, 'decrypt:392')['status'], 'REJECT')
        self.assertEqual(registry.check(value, 'cyphersolver:392')['status'], 'CLEAR')

    def test_verified_server_error_is_not_a_cipher_fingerprint(self):
        seed = json.loads((ROOT/'research/NO_REPEAT_REGISTRY.json').read_text())
        error_hash = '1e47167c4db694fe06f61f4c5650ac54eff2ce3ee2eff9dea78c7f15aa55b606'
        self.assertFalse(any(f['sha256'] == error_hash for r in seed['records']
                             for f in r['source_fingerprints']))
        record = next(r for r in seed['records'] if r['case_id'] == 'decrypt:1046')
        self.assertEqual(record['disposition'], 'skip')
        self.assertEqual(registry.check(seed, 'decrypt:1046')['status'], 'REJECT')

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
