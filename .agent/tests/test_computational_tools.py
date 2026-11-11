from __future__ import annotations
import json
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

if __name__ == "__main__":
    unittest.main()
