from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "serve_grill", SKILL / "scripts" / "serve_grill.py"
)
grill = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(grill)


class GrillTests(unittest.TestCase):
    def test_validation_preserves_explicit_decision_and_answer(self):
        data = grill.validate_session(
            {
                "title": "Demo",
                "status": "complete",
                "questions": [
                    {
                        "id": "a",
                        "question": "Choose?",
                        "recommendation": "A",
                        "tradeoff": "B",
                        "decision": "reject",
                        "answer": "C",
                    }
                ],
            }
        )
        self.assertEqual(data["questions"][0]["decision"], "reject")
        self.assertEqual(data["questions"][0]["answer"], "C")
        self.assertEqual(data["status"], "complete")

    def test_use_decision_drops_stale_answer(self):
        data = grill.validate_session(
            {
                "questions": [
                    {"question": "Choose?", "decision": "use", "answer": "stale"}
                ]
            }
        )
        self.assertEqual(data["questions"][0]["answer"], "")

    def test_migrates_legacy_recommendation_choice(self):
        data = grill.validate_session(
            {"questions": [{"question": "Choose?", "use_recommendation": True}]}
        )
        self.assertEqual(data["questions"][0]["decision"], "use")

    def test_atomic_write_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session.json"
            data = {"title": "Demo", "status": "open", "questions": []}
            grill.atomic_write(path, data)
            self.assertEqual(json.loads(path.read_text()), data)

    def test_rejects_missing_questions(self):
        with self.assertRaises(ValueError):
            grill.validate_session({"title": "Bad"})


if __name__ == "__main__":
    unittest.main()
