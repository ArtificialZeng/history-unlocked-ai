"""MIT-licensed, offline checker of retained scalar evidence; no solving."""
import argparse
import datetime as dt
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_MODULE_FILES = {
    "README.md", "THIRD_PARTY_NOTICES.md", "calls.json", "summary.json", "provenance.json",
    "schema.json", "verify_retained_trial.py", "test_verify.py",
    "licenses/MIT.txt", "licenses/CC-BY-NC-SA-4.0.txt", "licenses/UD_CZECH_PDTC_LICENSE.txt",
}

# These baseline scalar receipts were already extracted from the original retained record.
EXPECTED_BASELINE_COMPONENTS = {'all_quadgram_windows': 412,
 'all_window_average': -6.857167970786974,
 'constant_sentinel_score': -544.5466194152832,
 'fully_observed_average': -6.629670303921367,
 'fully_observed_quadgram_windows': 344,
 'fully_observed_score': -2280.60658454895,
 'score': -2825.1532039642334,
 'sentinel_containing_quadgram_windows': 68}

# Fixed definitions are code-owned; the JSON schema is a checked documentation copy.
EXPECTED_SCHEMA = {'schema': 'HC1527_NUMERIC_RECORD_SCHEMA_v2',
 'scope': 'Scalar-only field inventory enforced by the portable verifier; strict additional-property checks '
          'for each call/restart record.',
 'summary_fields': ['schema',
                    'case_id',
                    'status',
                    'evidence_role',
                    'fixed_configuration',
                    'counts',
                    'scores',
                    'runtime',
                    'inherited_independent_math_audit',
                    'inherited_blind_ai_content_audit',
                    'decision',
                    'cadence',
                    'identifiability',
                    'limitations'],
 'provenance_fields': ['schema',
                       'source_case_id',
                       'source_record_role',
                       'resource_pins',
                       'source_input_hash_role',
                       'call_records',
                       'aggregate_records',
                       'omitted_fields',
                       'licensing',
                       'root_successor_scalars_source_verified'],
 'call_fields': ['seed',
                 'restarts',
                 'steps',
                 'core_wall_seconds',
                 'started_utc',
                 'completed_utc',
                 'exit_code',
                 'input_sha256',
                 'call_id',
                 'kind',
                 'shuffle_seed',
                 'score',
                 'winner_restart',
                 'restart_scores',
                 'score_components',
                 'maximum_score_ties'],
 'score_component_fields': ['all_quadgram_windows',
                            'all_window_average',
                            'constant_sentinel_score',
                            'fully_observed_average',
                            'fully_observed_quadgram_windows',
                            'fully_observed_score',
                            'known_character_count',
                            'sentinel_containing_quadgram_windows'],
 'restart_fields': ['restart', 'score'],
 'hash_algorithm': 'SHA-256',
 'number_policy': 'finite JSON numbers only',
 'semantic_constraints': 'Fixed 100-call sequence, 18 ordered restarts per call, first maximum, plus-one '
                         'rank and prospective budgets enforced by verify_retained_trial.py.',
 'json_layouts': {'calls.json': {'type': 'object',
                                 'fields': {'schema': {'type': 'string'},
                                            'calls': {'type': 'array',
                                                      'items': {'type': 'object',
                                                                'fields': {'seed': {'type': 'integer'},
                                                                           'restarts': {'type': 'integer'},
                                                                           'steps': {'type': 'integer'},
                                                                           'core_wall_seconds': {'type': 'float'},
                                                                           'started_utc': {'type': 'string'},
                                                                           'completed_utc': {'type': 'string'},
                                                                           'exit_code': {'type': 'integer'},
                                                                           'input_sha256': {'type': 'string'},
                                                                           'call_id': {'type': 'string'},
                                                                           'kind': {'type': 'string'},
                                                                           'shuffle_seed': {'type': 'oneof',
                                                                                            'options': [{'type': 'null'},
                                                                                                        {'type': 'integer'}]},
                                                                           'score': {'type': 'float'},
                                                                           'winner_restart': {'type': 'integer'},
                                                                           'restart_scores': {'type': 'array',
                                                                                              'items': {'type': 'object',
                                                                                                        'fields': {'restart': {'type': 'integer'},
                                                                                                                   'score': {'type': 'float'}}}},
                                                                           'score_components': {'type': 'object',
                                                                                                'fields': {'all_quadgram_windows': {'type': 'integer'},
                                                                                                           'all_window_average': {'type': 'float'},
                                                                                                           'constant_sentinel_score': {'type': 'float'},
                                                                                                           'fully_observed_average': {'type': 'float'},
                                                                                                           'fully_observed_quadgram_windows': {'type': 'integer'},
                                                                                                           'fully_observed_score': {'type': 'float'},
                                                                                                           'known_character_count': {'type': 'integer'},
                                                                                                           'sentinel_containing_quadgram_windows': {'type': 'integer'}}},
                                                                           'maximum_score_ties': {'type': 'integer'}}}}}},
                  'summary.json': {'type': 'object',
                                   'fields': {'schema': {'type': 'string'},
                                              'case_id': {'type': 'string'},
                                              'status': {'type': 'string'},
                                              'evidence_role': {'type': 'string'},
                                              'fixed_configuration': {'type': 'object',
                                                                      'fields': {'solver_seed': {'type': 'integer'},
                                                                                 'shuffle_seed_first': {'type': 'integer'},
                                                                                 'shuffle_seed_last': {'type': 'integer'},
                                                                                 'restarts': {'type': 'integer'},
                                                                                 'steps': {'type': 'integer'},
                                                                                 'positive_calls': {'type': 'integer'},
                                                                                 'negative_calls': {'type': 'integer'},
                                                                                 'max_parallel_core_processes': {'type': 'integer'},
                                                                                 'per_core_timeout_seconds': {'type': 'integer'},
                                                                                 'max_aggregate_core_wall_seconds': {'type': 'integer'},
                                                                                 'whole_trial_seconds': {'type': 'integer'},
                                                                                 'fully_observed_average_gate': {'type': 'float'},
                                                                                 'tie_rule': {'type': 'string'}}},
                                              'counts': {'type': 'object',
                                                         'fields': {'positive_calls': {'type': 'integer'},
                                                                    'shuffle_calls': {'type': 'integer'},
                                                                    'total_calls': {'type': 'integer'},
                                                                    'restarts': {'type': 'integer'},
                                                                    'nominal_iteration_budget_total': {'type': 'integer'},
                                                                    'calls_with_tied_maximum': {'type': 'integer'}}},
                                              'scores': {'type': 'object',
                                                         'fields': {'positive': {'type': 'float'},
                                                                    'frequency_baseline': {'type': 'float'},
                                                                    'highest_shuffle': {'type': 'float'},
                                                                    'lowest_shuffle': {'type': 'float'},
                                                                    'positive_minus_baseline': {'type': 'float'},
                                                                    'positive_minus_highest_shuffle': {'type': 'float'},
                                                                    'null_ge_positive': {'type': 'integer'},
                                                                    'plus_one_p': {'type': 'float'},
                                                                    'denominator': {'type': 'integer'},
                                                                    'resolution': {'type': 'float'},
                                                                    'positive_components': {'type': 'object',
                                                                                            'fields': {'all_quadgram_windows': {'type': 'integer'},
                                                                                                       'all_window_average': {'type': 'float'},
                                                                                                       'constant_sentinel_score': {'type': 'float'},
                                                                                                       'fully_observed_average': {'type': 'float'},
                                                                                                       'fully_observed_quadgram_windows': {'type': 'integer'},
                                                                                                       'fully_observed_score': {'type': 'float'},
                                                                                                       'maximum_score_ties': {'type': 'integer'},
                                                                                                       'score': {'type': 'float'},
                                                                                                       'sentinel_containing_quadgram_windows': {'type': 'integer'},
                                                                                                       'winner_restart': {'type': 'integer'}}},
                                                                    'baseline_components': {'type': 'object',
                                                                                            'fields': {'all_quadgram_windows': {'type': 'integer'},
                                                                                                       'all_window_average': {'type': 'float'},
                                                                                                       'constant_sentinel_score': {'type': 'float'},
                                                                                                       'fully_observed_average': {'type': 'float'},
                                                                                                       'fully_observed_quadgram_windows': {'type': 'integer'},
                                                                                                       'fully_observed_score': {'type': 'float'},
                                                                                                       'score': {'type': 'float'},
                                                                                                       'sentinel_containing_quadgram_windows': {'type': 'integer'}}}}},
                                              'runtime': {'type': 'object',
                                                          'fields': {'aggregate_core_wall_seconds': {'type': 'float'},
                                                                     'min_core_wall_seconds': {'type': 'float'},
                                                                     'max_core_wall_seconds': {'type': 'float'},
                                                                     'whole_trial_elapsed_seconds': {'type': 'float'},
                                                                     'actual_peak_core_process_overlap': {'type': 'integer'}}},
                                              'inherited_independent_math_audit': {'type': 'object',
                                                                                   'fields': {'status': {'type': 'string'},
                                                                                              'checks': {'type': 'integer'},
                                                                                              'failures': {'type': 'integer'},
                                                                                              'public_checker_reexecutes_original_audit': {'type': 'boolean'}}},
                                              'inherited_blind_ai_content_audit': {'type': 'object',
                                                                                   'fields': {'unique_streams_reviewed': {'type': 'integer'},
                                                                                              'coherent_streams': {'type': 'integer'},
                                                                                              'partial_streams': {'type': 'integer'},
                                                                                              'incoherent_streams': {'type': 'integer'},
                                                                                              'complete_connected_message_established': {'type': 'boolean'},
                                                                                              'whole_content_pass': {'type': 'boolean'}}},
                                              'decision': {'type': 'object',
                                                           'fields': {'initial_feasibility_judgment': {'type': 'integer'},
                                                                      'post_review_continuation_judgment': {'type': 'integer'},
                                                                      'strict_continuation_threshold': {'type': 'integer'},
                                                                      'complete_reading_established': {'type': 'boolean'},
                                                                      'judgments_are_probabilities': {'type': 'boolean'}}},
                                              'cadence': {'type': 'object',
                                                          'fields': {'actual_cli_to_first_safe_seconds': {'type': 'float'},
                                                                     'required_max_seconds': {'type': 'integer'},
                                                                     'cadence_pass': {'type': 'boolean'},
                                                                     'worker_internal_first_safe_claim_seconds': {'type': 'integer'},
                                                                     'worker_internal_claim_substitutes_for_cli_timing': {'type': 'boolean'},
                                                                     'numeric_artifact_validity_independent_of_cadence': {'type': 'boolean'}}},
                                              'identifiability': {'type': 'object',
                                                                  'fields': {'model_positions': {'type': 'integer'},
                                                                             'unknown_sentinel_positions_retained': {'type': 'integer'},
                                                                             'unobserved_numeric_types': {'type': 'integer'},
                                                                             'unobserved_letter_permutations_with_identical_body_output': {'type': 'integer'},
                                                                             'distinct_literal_outputs_among_target_restarts': {'type': 'integer'},
                                                                             'distinct_observed_key_assignments_among_target_restarts': {'type': 'integer'},
                                                                             'distinct_full_key_assignments_among_target_restarts': {'type': 'integer'},
                                                                             'top_two_restart_score_gap': {'type': 'float'},
                                                                             'body_marks_outside_hypothesis': {'type': 'integer'},
                                                                             'footer_inventory_items_outside_hypothesis': {'type': 'integer'}}},
                                              'limitations': {'type': 'array', 'items': {'type': 'string'}}}},
                  'provenance.json': {'type': 'object',
                                      'fields': {'schema': {'type': 'string'},
                                                 'source_case_id': {'type': 'string'},
                                                 'source_record_role': {'type': 'string'},
                                                 'resource_pins': {'type': 'object',
                                                                   'fields': {'core_sha256': {'type': 'string'},
                                                                              'model_sha256': {'type': 'string'},
                                                                              'frequency_sha256': {'type': 'string'},
                                                                              'fixed_config_sha256': {'type': 'string'},
                                                                              'runner_sha256': {'type': 'string'},
                                                                              'binary_sha256': {'type': 'string'},
                                                                              'input_sha256': {'type': 'string'}}},
                                                 'source_input_hash_role': {'type': 'string'},
                                                 'call_records': {'type': 'array',
                                                                  'items': {'type': 'object',
                                                                            'fields': {'source_record': {'type': 'string'},
                                                                                       'sha256': {'type': 'string'},
                                                                                       'extracted_fields': {'type': 'array',
                                                                                                            'items': {'type': 'string'}}}}},
                                                 'aggregate_records': {'type': 'array',
                                                                       'items': {'type': 'object',
                                                                                 'fields': {'source_record': {'type': 'string'},
                                                                                            'sha256': {'type': 'string'},
                                                                                            'extraction_role': {'type': 'string'}}}},
                                                 'omitted_fields': {'type': 'array',
                                                                    'items': {'type': 'string'}},
                                                 'licensing': {'type': 'object',
                                                               'fields': {'original_code_and_new_documentation': {'type': 'string'},
                                                                          'numeric_scores_and_corpus_derived_aggregates': {'type': 'string'}}},
                                                 'root_successor_scalars_source_verified': {'type': 'boolean'}}}},
 'integer_policy': 'JSON integers only: booleans and floating-point values rejected',
 'float_policy': 'Finite JSON floating-point values only: booleans and integers rejected',
 'trust_policy': 'This document must equal the immutable definition in verifier code; editing and rehashing '
                 'it cannot expand allowed fields.'}
EXPECTED_RETAINED_CLAIMS = {'schema': 'HC1527_RETAINED_NUMERIC_SUMMARY_v1',
 'case_id': 'hcportal:1527',
 'status': 'STOP_CONFIDENCE_BELOW_CONTINUATION_GATE',
 'evidence_role': 'retained numeric arithmetic and integrity replay',
 'inherited_independent_math_audit': {'status': 'PASS_RETAINED_RUNTIME_INTERNAL_VALIDITY',
                                      'checks': 89640,
                                      'failures': 0,
                                      'public_checker_reexecutes_original_audit': False},
 'inherited_blind_ai_content_audit': {'unique_streams_reviewed': 4,
                                      'coherent_streams': 0,
                                      'partial_streams': 1,
                                      'incoherent_streams': 3,
                                      'complete_connected_message_established': False,
                                      'whole_content_pass': False},
 'decision': {'initial_feasibility_judgment': 83,
              'post_review_continuation_judgment': 79,
              'strict_continuation_threshold': 80,
              'complete_reading_established': False,
              'judgments_are_probabilities': False},
 'cadence': {'actual_cli_to_first_safe_seconds': 217.946343,
             'required_max_seconds': 120,
             'cadence_pass': False,
             'worker_internal_first_safe_claim_seconds': 34,
             'worker_internal_claim_substitutes_for_cli_timing': False,
             'numeric_artifact_validity_independent_of_cadence': True},
 'identifiability': {'model_positions': 415,
                     'unknown_sentinel_positions_retained': 17,
                     'unobserved_numeric_types': 6,
                     'unobserved_letter_permutations_with_identical_body_output': 720,
                     'distinct_literal_outputs_among_target_restarts': 4,
                     'distinct_observed_key_assignments_among_target_restarts': 4,
                     'distinct_full_key_assignments_among_target_restarts': 17,
                     'top_two_restart_score_gap': 0.0,
                     'body_marks_outside_hypothesis': 15,
                     'footer_inventory_items_outside_hypothesis': 14},
 'limitations': ['Conditional order signal under one fixed modern-language scoring model; no historical '
                 'accuracy probability.',
                 'Numeric forward consistency does not establish a source glyph certificate, gap readings or '
                 'a complete connected message.',
                 'Positive maximum tied across 15 of 18 restarts; alternate literal outputs and 720 '
                 'unused-class completions remain.',
                 'Receipts document retained execution; they do not include complete optimization '
                 'trajectories or independent OS telemetry of every step.',
                 'Stopping this model does not prove the cipher impossible; no new target solver runs are '
                 'performed.']}
EXPECTED_PROVENANCE_CANONICAL_SHA256 = 'cac468b419fb5478de778288301eed8571c6639b0b98dbb0860a36e0e32872e3'


class InvalidEvidence(ValueError):
    pass



def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def validate_structure(value, rule, label, require):
    kind = rule["type"]
    if kind == "object":
        require(type(value) is dict, label + ": object required")
        require(set(value) == set(rule["fields"]), label + ": exact nested field inventory")
        for field, subrule in rule["fields"].items():
            validate_structure(value[field], subrule, label + "." + field, require)
    elif kind == "array":
        require(type(value) is list, label + ": array required")
        for index, item in enumerate(value):
            validate_structure(item, rule["items"], label + "[" + str(index) + "]", require)
    elif kind == "integer":
        require(type(value) is int, label + ": strict JSON integer required")
    elif kind == "float":
        require(type(value) is float and math.isfinite(value), label + ": finite JSON float required")
    elif kind == "boolean":
        require(type(value) is bool, label + ": JSON boolean required")
    elif kind == "string":
        require(type(value) is str, label + ": JSON string required")
    elif kind == "null":
        require(value is None, label + ": null required")
    elif kind == "oneof":
        # The only optional scalar is the positive call's null shuffle seed.
        require(value is None or type(value) is int, label + ": null or strict JSON integer required")
    else:
        raise InvalidEvidence("unknown immutable structure rule")

def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise InvalidEvidence("duplicate JSON field")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(InvalidEvidence("nonfinite JSON")))


def check(root=ROOT):
    count = 0

    def require(condition, message):
        nonlocal count
        count += 1
        if not condition:
            raise InvalidEvidence(message)

    def equal(a, b, message):
        require(type(a) is not bool and type(b) is not bool and
                isinstance(a, (int, float)) and isinstance(b, (int, float)) and
                math.isfinite(a) and math.isfinite(b) and
                math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-9), message)

    root = Path(root)
    manifest = load(root / "MODULE_SHA256.json")
    require(set(manifest) == {"schema", "files"}, "manifest shape")
    require(manifest["schema"] == "HC1527_MODULE_SHA256_v1", "manifest schema")
    paths = list(root.rglob("*"))
    for path in paths:
        require(not path.is_symlink(), "symlink in module inventory")
    actual = {str(p.relative_to(root)) for p in paths
              if p.is_file() and str(p.relative_to(root)) != "MODULE_SHA256.json"}
    require(actual == EXPECTED_MODULE_FILES, "immutable module file inventory; run documented commands with -B")
    require(set(manifest["files"]) == EXPECTED_MODULE_FILES, "immutable manifest file inventory")
    require(actual == set(manifest["files"]), "file inventory")
    for name, digest in manifest["files"].items():
        require(not Path(name).is_absolute() and ".." not in Path(name).parts, "manifest path")
        path = root / name
        require(not path.is_symlink(), "symlink")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, "file hash: " + name)
    schema_document = load(root / "schema.json")
    schema = EXPECTED_SCHEMA
    require(canonical(schema_document) == canonical(EXPECTED_SCHEMA), "schema document diverges from immutable code definition")
    s = load(root / "summary.json")
    payload = load(root / "calls.json")
    p = load(root / "provenance.json")
    validate_structure(payload, EXPECTED_SCHEMA["json_layouts"]["calls.json"], "calls", require)
    validate_structure(s, EXPECTED_SCHEMA["json_layouts"]["summary.json"], "summary", require)
    validate_structure(p, EXPECTED_SCHEMA["json_layouts"]["provenance.json"], "provenance", require)
    for field, expected in EXPECTED_RETAINED_CLAIMS.items():
        require(canonical(s[field]) == canonical(expected), "retained claim changed: " + field)
    require(hashlib.sha256(canonical(p).encode("utf-8")).hexdigest() == EXPECTED_PROVENANCE_CANONICAL_SHA256,
            "provenance source hashes, extraction inventory or attribution changed")
    require(set(payload) == {"schema", "calls"}, "call envelope")
    require(payload["schema"] == "HC1527_RETAINED_NUMERIC_CALLS_v1", "call schema")
    require(set(s) == set(schema["summary_fields"]), "summary fields")
    require(set(p) == set(schema["provenance_fields"]), "provenance fields")
    require(s["schema"] == "HC1527_RETAINED_NUMERIC_SUMMARY_v1", "summary schema")
    require(s["case_id"] == "hcportal:1527", "case identity")
    cfg = s["fixed_configuration"]
    expected_cfg = {"solver_seed": 2026101457, "shuffle_seed_first": 2026101501,
                    "shuffle_seed_last": 2026101599, "restarts": 18, "steps": 100000,
                    "positive_calls": 1, "negative_calls": 99, "max_parallel_core_processes": 2,
                    "per_core_timeout_seconds": 60, "max_aggregate_core_wall_seconds": 6000,
                    "whole_trial_seconds": 2400, "fully_observed_average_gate": -4.7,
                    "tie_rule": "original_core_max_score_first_tie"}
    require(cfg == expected_cfg, "fixed prospective configuration")
    calls = payload["calls"]
    require(len(calls) == 100, "100 calls required")
    walls, scores, events = [], [], []
    tied_calls = 0
    total_restarts = 0
    for i, call in enumerate(calls):
        label = "positive" if i == 0 else "shuffle_" + str(2026101500 + i)
        require(set(call) == set(schema["call_fields"]), "unexpected/missing call field")
        require(call["call_id"] == label, "call identity and order")
        require(call["kind"] == ("positive" if i == 0 else "shuffle"), "call role")
        require(call["shuffle_seed"] == (None if i == 0 else 2026101500 + i), "shuffle seed")
        require(type(call["seed"]) is int and call["seed"] == 2026101457, "solver seed")
        require(call["restarts"] == 18 and call["steps"] == 100000, "restart/step budget")
        require(call["exit_code"] == 0, "successful recorded exit")
        require(isinstance(call["input_sha256"], str) and len(call["input_sha256"]) == 64 and
                all(x in "0123456789abcdef" for x in call["input_sha256"]), "opaque input hash")
        trials = call["restart_scores"]
        require(len(trials) == 18, "18 restart records per call")
        for n, trial in enumerate(trials):
            require(set(trial) == {"restart", "score"}, "restart scalar-only fields")
            require(type(trial["restart"]) is int and trial["restart"] == n, "restart order")
            equal(trial["score"], trial["score"], "finite restart score")
        best = max(t["score"] for t in trials)
        winner = next(t["restart"] for t in trials if t["score"] == best)
        ties = sum(t["score"] == best for t in trials)
        equal(call["score"], best, "restart maximum")
        require(call["winner_restart"] == winner, "first-maximum tie rule")
        require(call["maximum_score_ties"] == ties, "maximum tie count")
        tied_calls += ties > 1
        total_restarts += len(trials)
        components = call["score_components"]
        require(set(components) == set(schema["score_component_fields"]), "score component fields")
        require(components["known_character_count"] == 398, "known position count")
        require(components["all_quadgram_windows"] == 412 and
                components["fully_observed_quadgram_windows"] == 344 and
                components["sentinel_containing_quadgram_windows"] == 68, "window counts")
        equal(components["constant_sentinel_score"], -544.5466194152832, "constant sentinel score")
        equal(best, components["fully_observed_score"] + components["constant_sentinel_score"], "score decomposition")
        equal(components["all_window_average"], best / 412, "all window average")
        equal(components["fully_observed_average"], components["fully_observed_score"] / 344, "observed window average")
        wall = call["core_wall_seconds"]
        equal(wall, wall, "finite wall duration")
        require(0 < wall <= 60, "per-call wall budget")
        start = dt.datetime.fromisoformat(call["started_utc"])
        end = dt.datetime.fromisoformat(call["completed_utc"])
        require(start.utcoffset() == dt.timedelta(0) and end.utcoffset() == dt.timedelta(0), "UTC receipt")
        require(end >= start and abs((end - start).total_seconds() - wall) < 0.02, "receipt wall interval")
        events.extend([(start, 1), (end, -1)])
        walls.append(wall)
        scores.append(best)
    peak, live = 0, 0
    for _, delta in sorted(events, key=lambda x: (x[0], x[1])):
        live += delta
        peak = max(peak, live)
    require(live == 0 and peak <= 2, "receipt overlap budget")
    counts = s["counts"]
    require(counts == {"positive_calls": 1, "shuffle_calls": 99, "total_calls": 100,
                       "restarts": total_restarts, "nominal_iteration_budget_total": total_restarts * 100000,
                       "calls_with_tied_maximum": tied_calls}, "budget and count aggregates")
    sc = s["scores"]
    equal(sc["positive"], scores[0], "aggregate positive")
    equal(sc["positive"], -2138.6552350521088, "retained positive anchor")
    equal(sc["frequency_baseline"], -2825.1532039642334, "retained baseline anchor")
    equal(sc["highest_shuffle"], max(scores[1:]), "highest shuffle")
    equal(sc["lowest_shuffle"], min(scores[1:]), "lowest shuffle")
    equal(sc["positive_minus_baseline"], scores[0] - sc["frequency_baseline"], "baseline score difference")
    equal(sc["positive_minus_highest_shuffle"], scores[0] - max(scores[1:]), "null score difference")
    ge = sum(x >= scores[0] for x in scores[1:])
    require(sc["null_ge_positive"] == ge and sc["denominator"] == 100, "conditional rank count")
    equal(sc["plus_one_p"], (1 + ge) / 100, "plus-one conditional rank")
    equal(sc["resolution"], 1 / 100, "conditional resolution")
    require(calls[0]["score_components"]["fully_observed_average"] >= cfg["fully_observed_average_gate"], "prospective heuristic gate")
    component_pairs = [("positive", sc["positive_components"]), ("baseline", sc["baseline_components"])]
    # Check counts before division, then link every duplicate scalar to its receipt.
    for name, components in component_pairs:
        require(components["all_quadgram_windows"] > 0 and components["fully_observed_quadgram_windows"] > 0,
                name + " window denominators")
        require(components["sentinel_containing_quadgram_windows"] >= 0 and
                components["all_quadgram_windows"] == components["fully_observed_quadgram_windows"] +
                components["sentinel_containing_quadgram_windows"], name + " window count consistency")
    positive_receipt = dict(calls[0]["score_components"], score=calls[0]["score"],
                            winner_restart=calls[0]["winner_restart"],
                            maximum_score_ties=calls[0]["maximum_score_ties"])
    for field, value in sc["positive_components"].items():
        require(field in positive_receipt and canonical(value) == canonical(positive_receipt[field]),
                "positive component linkage: " + field)
    equal(sc["baseline_components"]["score"], sc["frequency_baseline"], "baseline component score linkage")
    for field, expected in EXPECTED_BASELINE_COMPONENTS.items():
        require(canonical(sc["baseline_components"][field]) == canonical(expected),
                "baseline retained component: " + field)
    for field in ["all_quadgram_windows", "fully_observed_quadgram_windows", "sentinel_containing_quadgram_windows"]:
        require(sc["baseline_components"][field] == calls[0]["score_components"][field],
                "baseline same-input mask windows: " + field)
    for name, components in component_pairs:
        total = sc["positive"] if name == "positive" else sc["frequency_baseline"]
        equal(total, components["fully_observed_score"] + components["constant_sentinel_score"], name + " decomposition")
        equal(components["all_window_average"], total / components["all_quadgram_windows"], name + " mean")
        equal(components["fully_observed_average"], components["fully_observed_score"] / components["fully_observed_quadgram_windows"], name + " observed mean")
    require(sc["positive_components"]["maximum_score_ties"] == calls[0]["maximum_score_ties"] == 15, "positive tie limitation")
    runtime = s["runtime"]
    equal(runtime["aggregate_core_wall_seconds"], sum(walls), "aggregate core wall")
    equal(runtime["min_core_wall_seconds"], min(walls), "minimum core wall")
    equal(runtime["max_core_wall_seconds"], max(walls), "maximum core wall")
    require(runtime["actual_peak_core_process_overlap"] == peak, "reported receipt overlap")
    require(sum(walls) <= 6000 and 0 < runtime["whole_trial_elapsed_seconds"] <= 2400, "aggregate budgets")
    span = (max(t for t, d in events) - min(t for t, d in events)).total_seconds()
    require(span <= runtime["whole_trial_elapsed_seconds"] + 0.02, "receipt span inside trial")
    require(s["decision"] == {"initial_feasibility_judgment": 83, "post_review_continuation_judgment": 79,
                            "strict_continuation_threshold": 80, "complete_reading_established": False,
                            "judgments_are_probabilities": False}, "stopped decision limits")
    require(s["status"] == "STOP_CONFIDENCE_BELOW_CONTINUATION_GATE", "stop retained")
    cadence = s["cadence"]
    equal(cadence["actual_cli_to_first_safe_seconds"], 217.946343, "actual CLI cadence")
    require(cadence["required_max_seconds"] == 120 and cadence["cadence_pass"] is False and
            cadence["actual_cli_to_first_safe_seconds"] > cadence["required_max_seconds"], "timing failure disclosed")
    require(cadence["worker_internal_claim_substitutes_for_cli_timing"] is False and
            cadence["numeric_artifact_validity_independent_of_cadence"] is True, "timing scope")
    content = s["inherited_blind_ai_content_audit"]
    require(content == {"unique_streams_reviewed": 4, "coherent_streams": 0, "partial_streams": 1,
                        "incoherent_streams": 3, "complete_connected_message_established": False,
                        "whole_content_pass": False}, "inherited AI-content limits")
    audit = s["inherited_independent_math_audit"]
    require(audit["checks"] == 89640 and audit["failures"] == 0 and
            audit["public_checker_reexecutes_original_audit"] is False, "inherited audit scope")
    identity = s["identifiability"]
    require(identity["unobserved_numeric_types"] == 6 and
            identity["unobserved_letter_permutations_with_identical_body_output"] == math.factorial(6), "unused class completions")
    require(identity["distinct_literal_outputs_among_target_restarts"] == 4 and
            identity["top_two_restart_score_gap"] == 0, "alternate output limitations")
    require(len(p["call_records"]) == 200, "extraction record count")
    for pin in p["resource_pins"].values():
        require(isinstance(pin, str) and len(pin) == 64 and all(x in "0123456789abcdef" for x in pin), "opaque pin format")
    for record in p["call_records"] + p["aggregate_records"]:
        require("/" not in record["source_record"] and "\\" not in record["source_record"], "public source record identifier")
        require(len(record["sha256"]) == 64 and all(x in "0123456789abcdef" for x in record["sha256"]), "extraction source hash")
    require(p["licensing"] == {"original_code_and_new_documentation": "MIT",
                              "numeric_scores_and_corpus_derived_aggregates": "CC-BY-NC-SA-4.0"}, "licence scope")
    return {"status": "PASS_RETAINED_NUMERIC_EVIDENCE", "new_public_checks": count,
            "calls_recomputed": len(calls), "restarts_recomputed": total_restarts,
            "conditional_plus_one_p": (1 + ge) / 100, "timing_compliance": "FAIL_RETAINED",
            "original_independent_audit_reexecuted": False, "new_solver_calls": 0,
            "complete_historical_reading_established": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.root), indent=2))
    except (InvalidEvidence, KeyError, TypeError, ValueError, OSError) as error:
        print(json.dumps({"status": "FAIL", "reason": str(error)}))
        sys.exit(1)
