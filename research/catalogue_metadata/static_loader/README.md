# Portable static AST metadata tracer

A small, nonexecuting JavaScript dependency tracer with four synthetic regression controls. It uses vendored Acorn 8.19.0 and requires no package installation.

## Run the controls

Use Node.js 22 or newer. From the repository root:

```sh
node research/catalogue_metadata/static_loader/check_controls.mjs
```

The runner invokes the harness with the four bundled fixture strings; it does not run their JavaScript, contact their resource names, or use a browser. It reports each result and an `all_pass` flag. `FIXTURE_RESULTS.json` preserves the actual release verification output.

The four unchanged controls cover:

- Two chained `.then` calls sharing a start offset, with a direct literal resource.
- A lexical loader wrapper returning a literal resource chain.
- A caller-described in-page data container.
- A generic `.get('lang')` expression that must remain unresolved rather than become a resource.

## API

```js
import { trace } from './generic_identity_trace.mjs';
const result = trace(code, tags, query);
```

`code` is caller-supplied JavaScript text. `query` selects a `.then` call by `thenStart`, `thenEnd`, `callbackStart`, and `callbackEnd`; all are Acorn offsets in that text. `scriptIndex` is optional descriptive metadata. `tags` is an optional caller-supplied map from element IDs to tag metadata, used when the chain reaches a literal DOM selector. This package does not extract HTML or verify those supplied tag descriptions.

The result contains a bounded node/edge trace, static resource or container metadata, and unresolved reasons. Selection uses complete call and callback ranges; visited nodes use object identity through `WeakSet`. Up to 30 dependency nodes are traced. Parsing and indexing the input are not subject to that 30-node limit.

Only a complete string literal passed directly to `fetch` can qualify as a static resource. Variables, concatenations, templates and dynamic arguments remain UNKNOWN in `unresolved_nodes`; the tracer does not construct guessed URLs. Array and object payloads are reported by location/type rather than traversed for their values. A reported resource or container may coexist with an unresolved branch; those reasons remain in the output.

## Validation and limits

Validation covers only the four bundled synthetic fixtures. The API can accept other JavaScript text and does not certify that input as synthetic or classify its provenance. The output's `validation_scope` describes the completed validation, not the origin of a caller's input.

This is a conservative syntax tool, not a general JavaScript evaluator or complete data-flow analyzer. It does not prove runtime reachability, URL validity, asynchronous side effects, or complete lexical semantics. Unsupported syntax, ambiguous definitions and dynamic inputs remain unresolved. It returns metadata from the selected chain and does not emit a full AST. No real-source validation or new analysis feature is included in this release candidate.

`PROVENANCE.json` records the original file hashes, release hashes and the five small portability/reporting edits. Fixture bytes and both vendored dependency files are unchanged. The repository-level `CODE_CORE_MANIFEST.json` covers this public integration. The original candidate manifest is retained locally; its hash is recorded in `PROVENANCE.json`.

## Third-party dependency

Acorn 8.19.0 is distributed under the MIT license. The original license is retained at `vendor/acorn/LICENSE`; see `THIRD_PARTY_LICENSES.md` for its notice and distribution link. The Acorn license applies to that dependency. Licensing of the surrounding project is determined by its repository license.
