/** Replay only frozen synthetic indexed-cell controls, with no historical inputs. */
import {runFrozenValidation} from '../methods/indexed_cells/run_validation.mjs';
import {verifyFrozenControls} from '../methods/indexed_cells/verify_frozen_controls.mjs';

const validation = await runFrozenValidation();
const independent = await verifyFrozenControls();
console.log(JSON.stringify({
  status: validation.status === 'PASS_SOFTWARE_SCOPE' && independent.status === 'PASS_SOFTWARE_SCOPE' ? 'PASS' : 'FAIL',
  scope: 'Frozen synthetic indexed-cell software only; no historical attack',
  validation_status: validation.status,
  independent_status: independent.status,
  known_answer_fixtures: validation.known_answers.length,
  refusal_controls: validation.refusals.length,
  enumeration: validation.enumeration,
  failures: [...validation.failures, ...independent.failures],
  historical_inputs: 0,
}, null, 2));
if (validation.status !== 'PASS_SOFTWARE_SCOPE' || independent.status !== 'PASS_SOFTWARE_SCOPE' ||
    validation.failures.length || independent.failures.length) {
  process.exitCode = 1;
}
