/** Run the four fixed synthetic fixtures offline; return a failing exit status on failure. */
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const fixture = new URL('./SYNTHETIC_FIXTURE_INPUTS.json', import.meta.url);
const harness = fileURLToPath(new URL('./fixture_harness.mjs', import.meta.url));
const report = JSON.parse(execFileSync(process.execPath, [harness], {
  input: readFileSync(fixture), encoding: 'utf8', timeout: 30000,
}));
const pass = report.all_pass === true && report.fixture_count === 4 &&
  report.reports.length === 4 && report.reports.every(row => row.pass === true);
console.log(JSON.stringify({
  status: pass ? 'PASS_SYNTHETIC_SOFTWARE_ONLY' : 'FAIL',
  fixture_total: report.fixture_count,
  fixtures_passed: report.reports.filter(row => row.pass).length,
  validation_scope: report.validation_scope,
  page_JS_execution: report.page_JS_execution,
  network_requests: report.network_requests,
  unresolved_results_are_preserved: true,
}, null, 2));
if (!pass) process.exitCode = 1;
