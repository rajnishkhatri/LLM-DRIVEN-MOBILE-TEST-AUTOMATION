"""Gate 5 (F2, worker C): the judge is a stub guarded by the calibration gate.
Verdicts carry no authority until TPR and TNR >= 0.9 on the labeled slice; the
gate asserts the guard, not verdict quality (eval-spec §7, §9)."""
import pytest

from ari_demo.evals import judge


def test_rubric_version_pinned():
    assert judge.RUBRIC_VERSION == "faithfulness-v1"


def test_judge_uncalibrated_offline():
    assert judge.is_calibrated() is False, "offline has no human-labeled slice"


def test_judge_has_no_authority_before_calibration():
    with pytest.raises((judge.CalibrationError, NotImplementedError)):
        judge.judge_faithfulness("Cash is USD 48.2M.", [])
