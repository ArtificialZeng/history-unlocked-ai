/**
 * Separate read-only fixture audit: no kernel or validation-runner import.
 * Only frozen synthetic fixture files and this package's locks are read.
 */
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {verifyPair} from './independent_verifier.mjs';

const readHere = name => readFile(new URL(name, import.meta.url), 'utf8');
const allowed = new Set([
  'controls.json','refusal_controls.json','validation_config.json',
  'kernel.mjs','independent_verifier.mjs','run_validation.mjs',
  'verify_frozen_controls.mjs','MATHEMATICAL_SPEC.md','README.md'
]);

export async function verifyFrozenControls() {
  const started = performance.now();
  const started_at_utc = new Date().toISOString();
  const inputLock = JSON.parse(await readHere('preimplementation_lock.json'));
  const softwareLock = JSON.parse(await readHere('software_lock_v1.json'));
  const integrity = [];
  for (const row of [...inputLock.files,...softwareLock.files]) {
    if (!allowed.has(row.path)) throw new Error('unregistered_file_in_lock: ' + row.path);
    const text = await readHere(row.path);
    const sha256 = createHash('sha256').update(text,'utf8').digest('hex');
    const match = sha256 === row.sha256 && Buffer.byteLength(text,'utf8') === row.bytes;
    integrity.push({path:row.path,sha256,match});
    if (!match) throw new Error('locked_file_integrity_failure: ' + row.path);
  }
  const fixtures = JSON.parse(await readHere('controls.json'));
  const results = fixtures.controls.map(fixture => {
    const result = verifyPair(fixture.alphabet,fixture.ciphertext,fixture.gold_tokens,fixture.gold_certificate);
    const exact_certificate = JSON.stringify(result.certificate) === JSON.stringify(fixture.gold_certificate);
    return {id:fixture.id,passed:result.ok && exact_certificate,exact_certificate,
      issues:result.issues,independent_certificate:result.certificate};
  });
  return {
    schema:'indexed-cell-independent-audit-v1',
    scope:'read-only synthetic relation/occurrence audit; no historical qualification',
    status:results.every(row => row.passed) ? 'PASS_SOFTWARE_SCOPE' : 'FAIL_SOFTWARE_SCOPE',
    started_at_utc,finished_at_utc:new Date().toISOString(),elapsed_ms:performance.now()-started,
    kernel_calls:0,verifier_calls:results.length,integrity,results,
    historical_inputs:0,language_scores:0,failures:results.filter(row => !row.passed)
  };
}
