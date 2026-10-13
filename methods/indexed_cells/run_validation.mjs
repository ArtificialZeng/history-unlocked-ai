/**
 * Read-only bounded validation entry point. Imports only this generic package.
 * Returned reports may be saved by a caller; this module itself never writes.
 */
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {decode, encode, IndexedCellValidationError} from './kernel.mjs';
import {verifyPair} from './independent_verifier.mjs';

const readHere = name => readFile(new URL(name, import.meta.url), 'utf8');
const digest = text => createHash('sha256').update(text, 'utf8').digest('hex');
const equal = (left, right) => JSON.stringify(left) === JSON.stringify(right);
const permittedFiles = new Set([
  'controls.json','refusal_controls.json','validation_config.json',
  'kernel.mjs','independent_verifier.mjs','run_validation.mjs',
  'verify_frozen_controls.mjs','MATHEMATICAL_SPEC.md','README.md'
]);

function forwardMatchesCertificate(ciphertext, alphabet, certificate) {
  if (ciphertext.length !== certificate.length || !Array.isArray(ciphertext.groups)) return false;
  if (ciphertext.groups.length !== alphabet.length) return false;
  const occurrences = [];
  for (const group of ciphertext.groups) {
    if (alphabet.filter(row => row.cell_id === group.cell_id).length !== 1) return false;
    if (ciphertext.groups.filter(other => other.cell_id === group.cell_id).length !== 1) return false;
    for (const position of group.indices) occurrences.push({position,cell_id:group.cell_id});
  }
  if (occurrences.length !== certificate.length) return false;
  return certificate.every(row => occurrences.filter(item =>
    item.position === row.position && item.cell_id === row.cell_id).length === 1) &&
    occurrences.every(item => certificate.filter(row =>
      row.position === item.position && row.cell_id === item.cell_id).length === 1);
}

export async function runFrozenValidation() {
  const started = performance.now();
  const started_at_utc = new Date().toISOString();
  const inputLock = JSON.parse(await readHere('preimplementation_lock.json'));
  const softwareLock = JSON.parse(await readHere('software_lock_v1.json'));
  const integrity = [];
  for (const item of [...inputLock.files, ...softwareLock.files]) {
    if (!permittedFiles.has(item.path)) throw new Error('unregistered_file_in_lock: ' + item.path);
    const body = await readHere(item.path);
    const actual = digest(body);
    const match = actual === item.sha256 && Buffer.byteLength(body, 'utf8') === item.bytes;
    integrity.push({path:item.path,sha256:actual,match});
    if (!match) throw new Error('locked_file_integrity_failure: ' + item.path);
  }
  const controls = JSON.parse(await readHere('controls.json'));
  const refusals = JSON.parse(await readHere('refusal_controls.json'));
  const config = JSON.parse(await readHere('validation_config.json'));
  const counts = {kernel_decode:0,kernel_encode:0,kernel_total:0,verifier:0};
  const failures = [];
  function kernelCall(operation, alphabet, input) {
    counts.kernel_total += 1;
    counts[operation === 'decode' ? 'kernel_decode' : 'kernel_encode'] += 1;
    if (counts.kernel_total > config.budgets.kernel_calls_max) throw new Error('kernel_budget_exceeded');
    return operation === 'decode' ? decode(alphabet,input) : encode(alphabet,input);
  }
  function verifierCall(...args) {
    counts.verifier += 1;
    if (counts.verifier > config.budgets.verifier_calls_max) throw new Error('verifier_budget_exceeded');
    return verifyPair(...args);
  }
  const inputsBefore = JSON.stringify({controls,refusals,config});
  const knownStart = performance.now();
  const knownAnswers = [];
  for (const fixture of controls.controls) {
    const decoded = kernelCall('decode',fixture.alphabet,fixture.ciphertext);
    const encoded = kernelCall('encode',fixture.alphabet,fixture.gold_tokens);
    const verification = verifierCall(fixture.alphabet,fixture.ciphertext,decoded,fixture.gold_certificate);
    const exactGold = equal(decoded,fixture.gold_tokens);
    const forwardCertificate = forwardMatchesCertificate(encoded,fixture.alphabet,fixture.gold_certificate);
    const exactCertificate = equal(verification.certificate,fixture.gold_certificate);
    const coveringAlphabet = fixture.alphabet.every(row => fixture.gold_tokens.includes(row.token));
    const passed = exactGold && forwardCertificate && verification.ok && exactCertificate;
    const row = {
      id:fixture.id,passed,token_count:decoded.length,alphabet_cells:fixture.alphabet.length,
      exact_gold:exactGold,forward_certificate:forwardCertificate,
      independent_verifier:verification.ok,exact_certificate:exactCertificate,covering_alphabet:coveringAlphabet,
      decoded_tokens:decoded,independent_certificate:verification.certificate
    };
    knownAnswers.push(row);
    if (!passed) failures.push({phase:'known_answer',id:fixture.id,result:row,issues:verification.issues});
  }
  const known_answer_ms = performance.now() - knownStart;

  const refusalStart = performance.now();
  const refusalResults = [];
  const independentIssueFor = {missing_indices:'occurrence_count_mismatch',duplicate_index:'duplicate_position'};
  for (const fixture of refusals.controls) {
    const alphabet = Object.hasOwn(fixture,'alphabet') ? fixture.alphabet : refusals.alphabet;
    const input = fixture.operation === 'decode' ? fixture.ciphertext : fixture.tokens;
    let rejected = false;
    let actual_code = null;
    let details = null;
    try { kernelCall(fixture.operation,alphabet,input); }
    catch (error) {
      rejected = error instanceof IndexedCellValidationError;
      actual_code = error.code ?? error.name;
      details = error.details ?? {message:error.message};
    }
    const passed = rejected && actual_code === fixture.expected_code;
    let independent = null;
    if (fixture.operation === 'decode') {
      const n = fixture.ciphertext?.length;
      const harmlessCandidate = Number.isSafeInteger(n) && n >= 0 && n <= 3 ? Array(n).fill('A') : [];
      const checked = verifierCall(alphabet,fixture.ciphertext,harmlessCandidate);
      const requiredIssue = independentIssueFor[fixture.expected_code] ?? fixture.expected_code;
      independent = {rejected:!checked.ok,required_issue:requiredIssue,
        found_required_issue:checked.issues.some(issue => issue.code === requiredIssue),issues:checked.issues};
      if (!independent.rejected || !independent.found_required_issue) {
        failures.push({phase:'independent_refusal',id:fixture.id,result:independent});
      }
    }
    const row = {id:fixture.id,operation:fixture.operation,passed,expected_code:fixture.expected_code,
      actual_code,details,independent};
    refusalResults.push(row);
    if (!passed) failures.push({phase:'refusal',id:fixture.id,result:row});
  }
  const refusal_ms = performance.now() - refusalStart;

  const enumerationStart = performance.now();
  const alphabet = config.enumeration.alphabet;
  const orderPermutations = [[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]];
  const certificateStream = createHash('sha256');
  let sequences = 0;
  let decodeVariants = 0;
  let enumerationFailures = 0;
  for (const length of config.enumeration.lengths) {
    for (let ordinal = 0; ordinal < alphabet.length ** length; ordinal += 1) {
      // Independent finite mathematical product: explicit vectors over the frozen alphabet.
      const tokens = [];
      for (let position = 0; position < length; position += 1) {
        const digit = Math.floor(ordinal / alphabet.length ** (length - position - 1)) % alphabet.length;
        tokens.push(alphabet[digit].token);
      }
      const certificate = tokens.map((token,offset) => ({
        position:offset + 1,cell_id:alphabet.filter(row => row.token === token)[0].cell_id,token
      }));
      certificateStream.update(JSON.stringify({length,ordinal,certificate}) + '\n','utf8');
      sequences += 1;
      const encoded = kernelCall('encode',alphabet,tokens);
      if (!forwardMatchesCertificate(encoded,alphabet,certificate)) {
        enumerationFailures += 1;
        failures.push({phase:'enumeration_encode',length,ordinal});
      }
      for (let permutation = 0; permutation < orderPermutations.length; permutation += 1) {
        for (const indexOrder of config.enumeration.index_orders) {
          // Construct ciphertext from the mathematical certificate relation,
          // without calling the encoder to generate a decoder input.
          const ciphertext = {length,groups:orderPermutations[permutation].map(cellNumber => {
            const cell_id = alphabet[cellNumber].cell_id;
            const indices = certificate.filter(row => row.cell_id === cell_id).map(row => row.position);
            if (indexOrder === 'descending') indices.reverse();
            return {cell_id,indices};
          })};
          const decoded = kernelCall('decode',alphabet,ciphertext);
          const verification = verifierCall(alphabet,ciphertext,decoded,certificate);
          decodeVariants += 1;
          if (!equal(decoded,tokens) || !verification.ok || !equal(verification.certificate,certificate)) {
            enumerationFailures += 1;
            failures.push({phase:'enumeration_decode',length,ordinal,permutation,indexOrder,
              decoded,expected:tokens,issues:verification.issues});
          }
        }
      }
    }
  }
  if (sequences !== config.enumeration.sequence_count || decodeVariants !== config.enumeration.decode_variants) {
    failures.push({phase:'enumeration_counts',sequences,decodeVariants});
  }
  const enumeration_ms = performance.now() - enumerationStart;
  const inputsUnchanged = inputsBefore === JSON.stringify({controls,refusals,config});
  if (!inputsUnchanged) failures.push({phase:'input_mutation'});
  return {
    schema:'indexed-cell-validation-result-v1',
    status:failures.length === 0 ? 'PASS_SOFTWARE_SCOPE' : 'FAIL_SOFTWARE_SCOPE',
    scope:'synthetic/software only; neither authentic-language calibration nor historical applicability',
    started_at_utc,finished_at_utc:new Date().toISOString(),
    elapsed_ms:performance.now() - started,
    phase_timings_ms:{known_answer:known_answer_ms,refusal:refusal_ms,enumeration:enumeration_ms},
    locks:{input_locked_at_utc:inputLock.locked_at_utc,software_locked_at_utc:softwareLock.locked_at_utc,integrity},
    known_answers:knownAnswers,
    refusals:refusalResults,
    enumeration:{
      alphabet_cells:alphabet.length,lengths:config.enumeration.lengths,sequences,
      cell_group_permutations:orderPermutations.length,index_orders:config.enumeration.index_orders,
      decode_variants:decodeVariants,failures:enumerationFailures,
      independent_certificate_stream_sha256:certificateStream.digest('hex'),
      scope:'Exhaustive finite token-vector domain over this three-token alphabet and lengths 0..5; all six group orders and only the two registered index orders. Some short/empty index-order variants are identical. Mathematical/software consistency only.'
    },
    counts,budgets:config.budgets,inputs_unchanged:inputsUnchanged,
    historical_inputs:0,historical_method_calls:0,language_scores:0,source_reads:0,
    random_seed:config.random_seed,randomized_search:false,
    failures
  };
}
