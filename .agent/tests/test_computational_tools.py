from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / ".agent" / "tools"
sys.path.insert(0, str(TOOLS))

import compose_workflow
import foxhole_rf_calc
import validate_evidence_ledger
import validate_skill
import validate_json_schema

class SkillValidationTests(unittest.TestCase):
    def test_valid_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "sample-skill"
            folder.mkdir()
            path = folder / "SKILL.md"
            path.write_text("""---
name: sample-skill
description: A test skill.
---
# Purpose
## Activation
## Inputs and preconditions
## Procedure
## Outputs
## Failure handling
## Acceptance criteria
""" + ("x" * 300), encoding="utf-8")
            self.assertEqual(validate_skill.validate(path), [])

    def test_directory_name_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "wrong-folder"
            folder.mkdir()
            path = folder / "SKILL.md"
            path.write_text("""---
name: right-name
description: A test skill.
---
# Purpose
## Activation
## Inputs
## Procedure
## Outputs
## Failure handling
## Acceptance criteria
""" + ("x" * 300), encoding="utf-8")
            self.assertTrue(any("does not match directory" in e for e in validate_skill.validate(path)))

    def test_repository_skills_pass_structural_lint(self):
        skills = sorted((ROOT / ".agent" / "skills").rglob("SKILL.md"))
        self.assertGreaterEqual(len(skills), 11)
        for path in skills:
            with self.subTest(path=str(path)):
                self.assertEqual(validate_skill.validate(path), [])

class WorkflowCompositionTests(unittest.TestCase):
    def make_root(self, root: Path):
        (root / ".agent/skills/a").mkdir(parents=True)
        (root / ".agent/skills/b").mkdir(parents=True)
        (root / ".agent/tools").mkdir(parents=True)
        (root / ".agent/skills/a/SKILL.md").write_text("skill a", encoding="utf-8")
        (root / ".agent/skills/b/SKILL.md").write_text("skill b", encoding="utf-8")
        (root / ".agent/tools/tool.py").write_text("# tool", encoding="utf-8")

    def test_valid_dag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)
            manifest = {
                "workflow_id": "test-flow", "version": "1",
                "steps": [
                    {"id": "first", "skill": "a"},
                    {"id": "second", "skill": "b", "depends_on": ["first"], "tools": [".agent/tools/tool.py"]}
                ]
            }
            result = compose_workflow.compose(manifest, root)
            self.assertTrue(result["ok"], result["errors"])
            self.assertEqual(result["order"], ["first", "second"])
            self.assertFalse(result["execution_performed"])

    def test_cycle_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)
            manifest = {
                "workflow_id": "cycle", "version": "1",
                "steps": [
                    {"id": "a", "skill": "a", "depends_on": ["b"]},
                    {"id": "b", "skill": "b", "depends_on": ["a"]}
                ]
            }
            result = compose_workflow.compose(manifest, root)
            self.assertFalse(result["ok"])
            self.assertTrue(any("cycle" in e for e in result["errors"]))

    def test_missing_dependency_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)
            result = compose_workflow.compose({
                "workflow_id": "missing", "version": "1",
                "steps": [{"id": "a", "skill": "a", "depends_on": ["absent"]}]
            }, root)
            self.assertFalse(result["ok"])
            self.assertTrue(any("unknown dependency" in e for e in result["errors"]))

    def test_tool_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)
            result = compose_workflow.compose({
                "workflow_id": "traversal", "version": "1",
                "steps": [{"id": "a", "skill": "a", "tools": ["../README.md"]}]
            }, root)
            self.assertFalse(result["ok"])
            self.assertTrue(any("under .agent/tools" in e for e in result["errors"]))

    def test_malformed_tools_array_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)
            result = compose_workflow.compose({
                "workflow_id": "bad-tools", "version": "1",
                "steps": [{"id": "a", "skill": "a", "tools": "tool.py"}]
            }, root)
            self.assertFalse(result["ok"])
            self.assertTrue(any("tools must be an array" in e for e in result["errors"]))

    def test_all_repository_workflows_compose(self):
        manifests = sorted((ROOT / ".agent" / "workflows").glob("*.json"))
        self.assertEqual(len(manifests), 3)
        for path in manifests:
            with self.subTest(path=str(path)):
                manifest = json.loads(path.read_text(encoding="utf-8"))
                result = compose_workflow.compose(manifest, ROOT)
                self.assertTrue(result["ok"], result["errors"])

class EvidenceLedgerTests(unittest.TestCase):
    def test_verified_claim_requires_evidence(self):
        ledger = {
            "sources": [{"id": "S1", "uri": "https://example.invalid/source"}],
            "claims": [{
                "id": "C1", "statement": "A scoped claim",
                "claim_status": "PROVED", "verification_status": "VERIFIED",
                "source_ids": ["S1"], "evidence": ["test-output.txt"]
            }]
        }
        self.assertEqual(validate_evidence_ledger.validate(ledger), [])

    def test_unsubstantiated_verified_claim_rejected(self):
        ledger = {
            "sources": [{"id": "S1", "uri": "https://example.invalid/source"}],
            "claims": [{
                "id": "C1", "statement": "A scoped claim",
                "claim_status": "ARGUMENT", "verification_status": "VERIFIED",
                "source_ids": ["S1"], "evidence": []
            }]
        }
        self.assertTrue(any("VERIFIED requires" in e for e in validate_evidence_ledger.validate(ledger)))

class RFCalculatorTests(unittest.TestCase):
    def test_lc_example(self):
        c = foxhole_rf_calc.resonant_capacitance(1_000_000, 250e-6)
        self.assertAlmostEqual(c, 101.321e-12, delta=0.01e-12)

    def test_inverse_lc(self):
        f = foxhole_rf_calc.resonant_frequency(250e-6, 101.321e-12)
        self.assertAlmostEqual(f, 1_000_000, delta=10)

    def test_bandwidth(self):
        self.assertAlmostEqual(foxhole_rf_calc.bandwidth_hz(1_000_000, 100), 10_000)

    def test_thermal_noise_positive(self):
        self.assertGreater(foxhole_rf_calc.thermal_noise_rms(10_000, 10_000), 0)

    def test_dbm_conversion(self):
        self.assertAlmostEqual(foxhole_rf_calc.dbm_to_watts(0), 0.001)

    def test_rectification_ratio(self):
        self.assertAlmostEqual(foxhole_rf_calc.rectification_ratio(20e-6, -2e-6), 10)

    def test_nonpositive_input_rejected(self):
        with self.assertRaises(ValueError):
            foxhole_rf_calc.resonant_frequency(0, 1e-12)

    def test_dbm_overflow_rejected(self):
        with self.assertRaises(ValueError):
            foxhole_rf_calc.dbm_to_watts(10_000)


class SchemaValidationTests(unittest.TestCase):
    def test_workflow_schema_accepts_all_manifests(self):
        schema = ROOT / ".agent/schemas/workflow.schema.json"
        manifests = sorted((ROOT / ".agent/workflows").glob("*.json"))
        self.assertEqual(len(manifests), 3)
        result = validate_json_schema.validate_instances(schema, manifests)
        self.assertTrue(result["ok"], result)

    def test_evidence_schema_accepts_fixture(self):
        schema = ROOT / ".agent/schemas/evidence-ledger.schema.json"
        fixture = ROOT / ".agent/tests/fixtures/evidence-ledger.valid.json"
        result = validate_json_schema.validate_instances(schema, [fixture])
        self.assertTrue(result["ok"], result)

    def test_workflow_schema_rejects_unknown_property(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.json"
            path.write_text(json.dumps({
                "workflow_id": "bad", "version": "1",
                "steps": [{"id": "one", "skill": "sample", "unexpected": True}]
            }), encoding="utf-8")
            result = validate_json_schema.validate_instances(
                ROOT / ".agent/schemas/workflow.schema.json", [path]
            )
            self.assertFalse(result["ok"])
            self.assertTrue(result["instances"][0]["errors"])


class CLISmokeTests(unittest.TestCase):
    def run_cli(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOLS / script), *args],
            cwd=ROOT, capture_output=True, text=True, timeout=20,
        )

    def test_validate_skill_cli_success(self):
        result = self.run_cli("validate_skill.py", ".agent/skills")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("RESULT: PASS", result.stdout)

    def test_compose_workflow_cli_success(self):
        result = self.run_cli(
            "compose_workflow.py", ".agent/workflows/repository-forensics.json"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"execution_performed": false', result.stdout)

    def test_evidence_ledger_cli_success(self):
        result = self.run_cli(
            "validate_evidence_ledger.py",
            ".agent/tests/fixtures/evidence-ledger.valid.json",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"ok": true', result.stdout)

    def test_evidence_ledger_cli_rejects_invalid_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.json"
            path.write_text(json.dumps({"sources": [], "claims": [{
                "id": "C1", "statement": "unsupported",
                "claim_status": "ARGUMENT", "verification_status": "VERIFIED",
                "source_ids": [], "evidence": []
            }]}), encoding="utf-8")
            result = self.run_cli("validate_evidence_ledger.py", str(path))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('"ok": false', result.stdout)

    def test_rf_calculator_cli_success(self):
        result = self.run_cli("foxhole_rf_calc.py", "dbm-to-watts", "--dbm", "0")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertAlmostEqual(json.loads(result.stdout)["power_w"], 0.001)

    def test_rf_calculator_cli_rejects_invalid_input(self):
        result = self.run_cli(
            "foxhole_rf_calc.py", "capacitance",
            "--frequency-hz", "0", "--inductance-h", "0.00025",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("must be finite and > 0", result.stderr)

    def test_schema_validator_cli_success(self):
        result = self.run_cli(
            "validate_json_schema.py",
            "--schema", ".agent/schemas/workflow.schema.json",
            ".agent/workflows/repository-forensics.json",
            ".agent/workflows/openclaw-runtime-composition.json",
            ".agent/workflows/foxhole-radio-lab.json",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"draft": "2020-12"', result.stdout)

    def test_schema_validator_cli_rejects_invalid_instance(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.json"
            path.write_text('{"unexpected": true}', encoding="utf-8")
            result = self.run_cli(
                "validate_json_schema.py",
                "--schema", ".agent/schemas/workflow.schema.json", str(path),
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('"ok": false', result.stdout)

if __name__ == "__main__":
    unittest.main()
