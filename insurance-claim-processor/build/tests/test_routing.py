from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claim_processor.config import EscalationPolicy
from claim_processor.models import ProcessingResult, ValidationResult
from claim_processor.routing import route_claim

_ROUTING_CONSTANT_NAMES = frozenset(
    {
        "AMOUNT_THRESHOLD",
        "DEFAULT_AMOUNT_THRESHOLD",
        "ESCALATION_THRESHOLD",
        "THRESHOLD",
    }
)


def _extracted(**overrides: object) -> dict:
    payload = {
        "claimant_name": "A. Claimant",
        "policy_number": "POL-1",
        "incident_date": "2026-01-01",
        "claim_amount": 100.0,
        "incident_description": "fender bender",
    }
    payload.update(overrides)
    return payload


def _result(**overrides: object) -> ProcessingResult:
    kwargs: dict = {
        "extracted_info": _extracted(),
        "summary": "ok",
        "citations": ["chunk-1"],
        "ungrounded": False,
        "validation": ValidationResult(accepted=True, flags=[]),
        "extract_model_id": "extract-resolved",
        "summary_model_id": "summary-resolved",
        "prompt_versions": {"extract_info": "1"},
    }
    kwargs.update(overrides)
    return ProcessingResult(**kwargs)


class RouteClaimTests(unittest.TestCase):
    def test_clean_claim_auto_approves(self) -> None:
        self.assertEqual(
            route_claim(_result(), EscalationPolicy()),
            "auto_approve",
        )

    def test_missing_keys_routes_to_review(self) -> None:
        result = _result(
            validation=ValidationResult(
                accepted=False,
                flags=["missing_keys:policy_number"],
            )
        )
        self.assertEqual(route_claim(result, EscalationPolicy()), "human_review")

    def test_invalid_json_routes_to_review(self) -> None:
        result = _result(
            validation=ValidationResult(accepted=False, flags=["invalid_json"])
        )
        self.assertEqual(route_claim(result, EscalationPolicy()), "human_review")

    def test_not_an_object_routes_to_review(self) -> None:
        result = _result(
            validation=ValidationResult(accepted=False, flags=["not_an_object"])
        )
        self.assertEqual(route_claim(result, EscalationPolicy()), "human_review")

    def test_empty_fields_routes_to_review_even_if_accepted(self) -> None:
        result = _result(
            validation=ValidationResult(
                accepted=True,
                flags=["empty_fields:policy_number"],
            )
        )
        self.assertEqual(route_claim(result, EscalationPolicy()), "human_review")

    def test_ungrounded_result_routes_to_review(self) -> None:
        result = _result(ungrounded=True)
        self.assertEqual(route_claim(result, EscalationPolicy()), "human_review")

    def test_ungrounded_flag_routes_to_review(self) -> None:
        result = _result(
            validation=ValidationResult(accepted=True, flags=["ungrounded"])
        )
        self.assertEqual(route_claim(result, EscalationPolicy()), "human_review")

    def test_missing_citations_routes_to_review(self) -> None:
        result = _result(
            validation=ValidationResult(accepted=True, flags=["missing_citations"])
        )
        self.assertEqual(route_claim(result, EscalationPolicy()), "human_review")

    def test_amount_above_threshold_routes_to_review(self) -> None:
        result = _result(extracted_info=_extracted(claim_amount=10000.01))
        self.assertEqual(route_claim(result, EscalationPolicy()), "human_review")

    def test_amount_equal_to_threshold_auto_approves(self) -> None:
        result = _result(extracted_info=_extracted(claim_amount=10000.0))
        self.assertEqual(route_claim(result, EscalationPolicy()), "auto_approve")

    def test_missing_amount_routes_to_review(self) -> None:
        extracted = _extracted()
        del extracted["claim_amount"]
        result = _result(extracted_info=extracted)
        self.assertEqual(route_claim(result, EscalationPolicy()), "human_review")

    def test_non_numeric_amount_routes_to_review(self) -> None:
        result = _result(extracted_info=_extracted(claim_amount="not-a-number"))
        self.assertEqual(route_claim(result, EscalationPolicy()), "human_review")

    def test_pii_ssn_routes_to_review(self) -> None:
        result = _result(
            validation=ValidationResult(accepted=True, flags=["pii_ssn"])
        )
        self.assertEqual(route_claim(result, EscalationPolicy()), "human_review")

    def test_pii_pan_routes_to_review(self) -> None:
        result = _result(
            validation=ValidationResult(accepted=True, flags=["pii_pan"])
        )
        self.assertEqual(route_claim(result, EscalationPolicy()), "human_review")

    def test_threshold_comes_from_policy_not_module_constant(self) -> None:
        result = _result(extracted_info=_extracted(claim_amount=15000.0))
        self.assertEqual(
            route_claim(result, EscalationPolicy(amount_threshold=20000.0)),
            "auto_approve",
        )
        self.assertEqual(
            route_claim(result, EscalationPolicy(amount_threshold=10000.0)),
            "human_review",
        )

        import claim_processor.routing as routing

        exported = {name for name in dir(routing) if name in _ROUTING_CONSTANT_NAMES}
        self.assertEqual(exported, set())
        tree = ast.parse(Path(routing.__file__).read_text())
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in _ROUTING_CONSTANT_NAMES:
                    self.fail(
                        f"routing threshold must live on EscalationPolicy, "
                        f"not module constant {target.id}"
                    )

    def test_force_review_flags_exact_and_prefix(self) -> None:
        exact = _result(
            validation=ValidationResult(accepted=True, flags=["fraud_signal"])
        )
        prefixed = _result(
            validation=ValidationResult(accepted=True, flags=["fraud_signal:high"])
        )
        policy = EscalationPolicy(force_review_flags=("fraud_signal",))
        self.assertEqual(route_claim(exact, policy), "human_review")
        self.assertEqual(route_claim(prefixed, policy), "human_review")
        self.assertEqual(route_claim(_result(), policy), "auto_approve")


if __name__ == "__main__":
    unittest.main()
