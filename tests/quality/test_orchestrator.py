"""Tests for src/quality/orchestrator.py.

No external dependencies -- all scorers are simple lambdas/mocks.
"""

import pytest

from src.quality.orchestrator import QualityOrchestrator, ScorerConfig, QualityResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_scorer(name: str, score: float, threshold: float = 0.5, weight: float = 1.0, required: bool = True):
    return ScorerConfig(
        name=name,
        scorer=lambda _c, s=score: s,
        threshold=threshold,
        weight=weight,
        required=required,
    )


# ---------------------------------------------------------------------------
# evaluate() tests
# ---------------------------------------------------------------------------


class TestEvaluate:
    def test_evaluate_all_pass(self):
        """All scorers above threshold -> accepted=True."""
        orch = QualityOrchestrator(
            scorers=[
                _make_scorer("a", 0.9, threshold=0.5),
                _make_scorer("b", 0.8, threshold=0.5),
            ]
        )
        result = orch.evaluate("candidate")
        assert result.accepted is True
        assert result.failure_reasons == []
        assert result.scores["a"] == pytest.approx(0.9)
        assert result.scores["b"] == pytest.approx(0.8)

    def test_evaluate_one_fails(self):
        """One below threshold -> accepted=False, failure_reasons populated."""
        orch = QualityOrchestrator(
            scorers=[
                _make_scorer("good", 0.9, threshold=0.5),
                _make_scorer("bad", 0.3, threshold=0.5),
            ]
        )
        result = orch.evaluate("candidate")
        assert result.accepted is False
        assert len(result.failure_reasons) == 1
        assert "bad" in result.failure_reasons[0]

    def test_composite_score_weighted_average(self):
        """Verify composite = weighted average of individual scores."""
        orch = QualityOrchestrator(
            scorers=[
                _make_scorer("a", 0.8, threshold=0.0, weight=2.0),
                _make_scorer("b", 0.4, threshold=0.0, weight=1.0),
            ]
        )
        result = orch.evaluate("x")
        # Weighted average: (2.0*0.8 + 1.0*0.4) / (2.0+1.0) = 2.0/3.0
        expected = (2.0 * 0.8 + 1.0 * 0.4) / 3.0
        assert result.composite_score == pytest.approx(expected, abs=1e-6)

    def test_soft_scorer_doesnt_reject(self):
        """required=False scorer below threshold -> still accepted=True."""
        orch = QualityOrchestrator(
            scorers=[
                _make_scorer("hard", 0.9, threshold=0.5, required=True),
                _make_scorer("soft", 0.1, threshold=0.5, required=False),
            ]
        )
        result = orch.evaluate("candidate")
        assert result.accepted is True
        assert result.failure_reasons == []


# ---------------------------------------------------------------------------
# run() tests
# ---------------------------------------------------------------------------


class TestRun:
    def test_run_accepts_first_passing(self):
        """Generator returns passing candidate -> accepted in round 1."""
        orch = QualityOrchestrator(
            scorers=[_make_scorer("s", 0.9, threshold=0.5)],
            n_candidates=2,
            max_rounds=3,
        )
        gen_calls = []

        def gen(**kwargs):
            gen_calls.append(1)
            return "good_candidate"

        result = orch.run(gen)
        assert result.accepted is True
        assert result.attempt == 1
        # Should stop after first passing candidate, not generate all
        assert len(gen_calls) == 1

    def test_run_exhausts_rounds(self):
        """All candidates fail -> returns best available with accepted=False."""
        orch = QualityOrchestrator(
            scorers=[_make_scorer("s", 0.3, threshold=0.5)],
            n_candidates=2,
            max_rounds=2,
        )

        result = orch.run(lambda **kw: "bad")
        assert result.accepted is False
        assert result.composite_score == pytest.approx(0.3)

    def test_on_reject_callback(self):
        """Verify on_reject callback is called on round failure."""
        callback_calls = []

        def on_reject(result):
            callback_calls.append(result)
            return {"extra_param": True}

        orch = QualityOrchestrator(
            scorers=[_make_scorer("s", 0.3, threshold=0.5)],
            n_candidates=1,
            max_rounds=3,
        )
        orch.run(lambda **kw: "bad", on_reject=on_reject)

        # on_reject is called after each failed round (except possibly the last)
        # With max_rounds=3: called after round 1, 2, and 3
        assert len(callback_calls) == 3

    def test_run_with_improving_generator(self):
        """Generator that improves each call eventually passes."""
        call_idx = [0]

        def gen(**kwargs):
            call_idx[0] += 1
            return f"candidate_{call_idx[0]}"

        scores = {}
        def scorer_fn(c):
            # 3rd candidate passes
            idx = int(c.split("_")[1])
            s = 0.3 if idx < 3 else 0.9
            scores[c] = s
            return s

        orch = QualityOrchestrator(
            scorers=[ScorerConfig(name="s", scorer=scorer_fn, threshold=0.5)],
            n_candidates=2,
            max_rounds=3,
        )
        result = orch.run(gen)
        # The 3rd candidate (round 2, candidate 1) should pass
        assert result.accepted is True
