#!/usr/bin/env python3
"""Offline audit probes. No network access, GitHub writes, or repository execution.

The gate predicates are transcribed from inspected source/patches. The YAML
fixture preserves a retrieved indentation defect inside a reduced wrapper.
Pagination uses synthetic records, not actual GitHub issue data.
Requires Python 3.10+ and PyYAML for the optional YAML probe.
"""
from __future__ import annotations

import io
import json
import platform
import sys
import unittest
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

HERE = Path(__file__).resolve().parent
HERMES_MAIN = "205645ee424163c7b6cfc032c331c3557797497b"
PR98563_HEAD = "68ca8e5b9ea2ec6be9fb4eecafef67ff2cd5896f"
PR108055_HEAD = "c907c76a4fae8aaef29158ba8fb9041ccaade233"
OPENCODE_HEAD = "95daf90670b7c039c436c85537da5fbfe2205b41"


def main_gate_accepts(needs: dict[str, dict[str, str]]) -> bool:
    """Exact blocking predicate from Hermes ci.yaml, NOT the whole job."""
    failed = [name for name, info in needs.items() if info['result'] == 'failure']
    return not failed


def donor_gate_accepts(needs: dict[str, dict[str, str]]) -> bool:
    """Blocking predicate from #98563, NOT an approval of that whole PR."""
    blocked = [name for name, info in needs.items()
               if info['result'] not in ('success', 'skipped')]
    return not blocked


def proposed_gate_accepts(
    needs: Any,
    expected_lanes: frozenset[str],
    permitted_skips: frozenset[str],
) -> bool:
    """Illustrative stronger contract. Not a deployed Hermes implementation.

    expected_lanes and permitted_skips must come from trusted policy, not from
    the candidate under test. Remote CI also needs exact-tree/run attestation.
    """
    if not isinstance(needs, dict) or not needs or not expected_lanes:
        return False
    if not expected_lanes.issubset(needs):
        return False
    if not permitted_skips.issubset(expected_lanes):
        return False
    for lane, info in needs.items():
        if not isinstance(info, dict):
            return False
        status = info.get('result')
        if status == 'success':
            continue
        if status == 'skipped' and lane in permitted_skips:
            continue
        return False
    return True


def mutable_offset_cleanup(total: int = 250, size: int = 100) -> tuple[list[int], list[int]]:
    """Model close-issues.ts paging over an open collection that it shrinks."""
    if total < 0 or size < 1:
        raise ValueError('Invalid pagination parameters')
    remaining = list(range(1, total + 1))
    closed: list[int] = []
    page = 1
    while True:
        items = remaining[(page - 1) * size:page * size]
        if not items:
            break
        closed.extend(items)
        removed = set(items)
        remaining = [number for number in remaining if number not in removed]
        page += 1
    return closed, remaining


def snapshot_cleanup(total: int = 250, size: int = 100) -> tuple[list[int], list[int]]:
    """Control: freeze candidate identities before simulating mutations."""
    if total < 0 or size < 1:
        raise ValueError('Invalid pagination parameters')
    snapshot = list(range(1, total + 1))
    remaining = set(snapshot)
    closed: list[int] = []
    for start in range(0, len(snapshot), size):
        batch = snapshot[start:start + size]
        closed.extend(batch)
        remaining.difference_update(batch)
    return closed, sorted(remaining)


# Reduced wrapper around the exact unindented comment/assignment retrieved from
# crazyief/hermes-agent at PR108055_HEAD, .github/workflows/ci.yaml lines 262-295.
BROKEN_YAML = '''name: reduced-source-fragment
jobs:
  aggregate:
    runs-on: ubuntu-latest
    steps:
      - name: Evaluate job results
        run: |
          echo "$NEEDS" | python3 -c "
          import json, sys
          needs = json.load(sys.stdin)
          # 'cancelled' counts as failed: cancel-in-progress concurrency cancels superseded runs, and
# a cancelled required job must not produce a green gate (the ❌ icon already hinted at this).
failed = [name for name, info in needs.items() if info['result'] in ('failure', 'cancelled')]
          print(failed)
          "
'''
REPAIRED_YAML = BROKEN_YAML.replace(
    '\n# a cancelled', '\n          # a cancelled'
).replace('\nfailed = ', '\n          failed = ')


class AuditProbes(unittest.TestCase):
    def test_current_accepts_cancelled(self):
        self.assertTrue(main_gate_accepts({'tests': {'result': 'cancelled'}}))

    def test_current_accepts_unrecognized_result(self):
        self.assertTrue(main_gate_accepts({'tests': {'result': 'unrecognized'}}))

    def test_current_rejects_failure(self):
        self.assertFalse(main_gate_accepts({'tests': {'result': 'failure'}}))

    def test_donor_rejects_cancelled(self):
        self.assertFalse(donor_gate_accepts({'tests': {'result': 'cancelled'}}))

    def test_donor_rejects_unrecognized_result(self):
        self.assertFalse(donor_gate_accepts({'tests': {'result': 'unrecognized'}}))

    def test_donor_preserves_skips(self):
        self.assertTrue(donor_gate_accepts({'docs': {'result': 'skipped'}}))

    def test_proposed_accepts_real_success_and_authorized_skip(self):
        self.assertTrue(proposed_gate_accepts(
            {'tests': {'result': 'success'}, 'docs': {'result': 'skipped'}},
            frozenset({'tests', 'docs'}), frozenset({'docs'})))

    def test_proposed_rejects_required_lane_skip(self):
        self.assertFalse(proposed_gate_accepts(
            {'tests': {'result': 'skipped'}}, frozenset({'tests'}), frozenset()))

    def test_proposed_rejects_missing_expected_lane(self):
        self.assertFalse(proposed_gate_accepts(
            {'detect': {'result': 'success'}}, frozenset({'detect', 'tests'}), frozenset()))

    def test_proposed_rejects_empty_report(self):
        self.assertFalse(proposed_gate_accepts({}, frozenset({'tests'}), frozenset()))

    def test_proposed_rejects_malformed_report(self):
        self.assertFalse(proposed_gate_accepts(
            {'tests': {}}, frozenset({'tests'}), frozenset()))

    @unittest.skipIf(yaml is None, 'PyYAML not installed')
    def test_retrieved_indentation_fragment_does_not_parse(self):
        with self.assertRaises(yaml.YAMLError):
            yaml.safe_load(BROKEN_YAML)

    @unittest.skipIf(yaml is None, 'PyYAML not installed')
    def test_restoring_indentation_is_positive_control(self):
        result = yaml.safe_load(REPAIRED_YAML)
        self.assertIn('failed = ', result['jobs']['aggregate']['steps'][0]['run'])

    def test_mutating_offsets_skip_candidates(self):
        closed, remaining = mutable_offset_cleanup()
        self.assertEqual(len(closed), 150)
        self.assertEqual(remaining, list(range(101, 201)))

    def test_snapshot_control_processes_all_candidates(self):
        closed, remaining = snapshot_cleanup()
        self.assertEqual(len(closed), 250)
        self.assertEqual(remaining, [])

    def test_invalid_page_size_is_refused(self):
        with self.assertRaises(ValueError):
            mutable_offset_cleanup(size=0)


def main() -> int:
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(AuditProbes))
    log = stream.getvalue()
    print(log)
    (HERE / 'probe_test_output.txt').write_text(log, encoding='utf-8')
    statuses = ['success', 'skipped', 'failure', 'cancelled', '', 'unrecognized']
    gate_rows = [{
        'input': status,
        'main_predicate_accepts': main_gate_accepts({'tests': {'result': status}}),
        'pr98563_predicate_accepts': donor_gate_accepts({'tests': {'result': status}}),
        'proposed_required_lane_accepts': proposed_gate_accepts(
            {'tests': {'result': status}}, frozenset({'tests'}), frozenset()),
    } for status in statuses]
    broken_error = None
    if yaml:
        try:
            yaml.safe_load(BROKEN_YAML)
        except yaml.YAMLError as exc:
            broken_error = str(exc)
    closed, remaining = mutable_offset_cleanup()
    snapshot_closed, snapshot_remaining = snapshot_cleanup()
    output = {
        'scope': 'Isolated source-predicate probes and synthetic counterexamples only',
        'not_performed': ['full repository tests', 'GitHub workflow execution',
                          'live issue closure', 'candidate integration-tree validation'],
        'python_version': platform.python_version(),
        'pyyaml_version': getattr(yaml, '__version__', None),
        'tests_run': result.testsRun,
        'failures': len(result.failures), 'errors': len(result.errors),
        'skips': len(result.skipped),
        'source_pins': {'hermes_main': HERMES_MAIN, 'pr98563_head': PR98563_HEAD,
                        'pr108055_head': PR108055_HEAD, 'opencode_dev': OPENCODE_HEAD},
        'gate_predicates': gate_rows,
        'yaml_fragment_parse_error': broken_error,
        'synthetic_pagination': {
            'initial_candidates': 250, 'page_size': 100,
            'mutable_offsets_processed': len(closed),
            'mutable_offsets_skipped': len(remaining),
            'snapshot_control_processed': len(snapshot_closed),
            'snapshot_control_skipped': len(snapshot_remaining),
        },
        'limitations': [
            'Gate predicates are transcribed, not imported from a checkout.',
            'YAML parsing uses a reduced source fragment with a synthetic wrapper.',
            'The missing-lane and empty-report checks are proposed defenses; no live reachability claim.',
            'Pagination models the inspected loop; it is not evidence of a specific production incident.',
        ],
    }
    (HERE / 'probe_results.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
