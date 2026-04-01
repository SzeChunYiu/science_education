"""Quality orchestrator: generate N candidates, score, accept best passing all thresholds."""
import logging
from dataclasses import dataclass, field
from typing import Any, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ScorerConfig:
    """Configuration for a single quality scorer."""
    name: str
    scorer: Callable[[Any], float]
    threshold: float
    weight: float = 1.0
    required: bool = True  # If False, failure logs warning but doesn't reject


@dataclass
class QualityResult:
    """Result of quality evaluation."""
    accepted: bool
    candidate: Any
    scores: dict[str, float] = field(default_factory=dict)
    composite_score: float = 0.0
    attempt: int = 0
    failure_reasons: list[str] = field(default_factory=list)


class QualityOrchestrator:
    """Generate candidates, score them, accept the best one passing all thresholds.

    Uses weighted average for ranking (not multiplicative) to avoid
    compound penalty problem.
    """

    def __init__(
        self,
        scorers: list[ScorerConfig],
        n_candidates: int = 4,
        max_rounds: int = 3,
        failure_log: Path | None = None,
    ):
        self.scorers = scorers
        self.n_candidates = n_candidates
        self.max_rounds = max_rounds
        self.failure_log = failure_log

    def evaluate(self, candidate: Any) -> QualityResult:
        """Score a single candidate against all scorers."""
        scores = {}
        failures = []

        for sc in self.scorers:
            try:
                score = sc.scorer(candidate)
                scores[sc.name] = score
                if score < sc.threshold and sc.required:
                    failures.append(
                        f"{sc.name}: {score:.3f} < {sc.threshold:.3f}"
                    )
                elif score < sc.threshold:
                    logger.warning(
                        f"Soft scorer {sc.name} below threshold: "
                        f"{score:.3f} < {sc.threshold:.3f}"
                    )
            except Exception as e:
                logger.error(f"Scorer {sc.name} failed: {e}")
                scores[sc.name] = 0.0
                if sc.required:
                    failures.append(f"{sc.name}: error - {e}")

        total_weight = sum(sc.weight for sc in self.scorers)
        composite = sum(
            sc.weight * scores.get(sc.name, 0.0) for sc in self.scorers
        ) / max(total_weight, 1e-8)

        return QualityResult(
            accepted=len(failures) == 0,
            candidate=candidate,
            scores=scores,
            composite_score=composite,
            failure_reasons=failures,
        )

    def run(
        self,
        generator: Callable[..., Any],
        on_reject: Callable[[QualityResult], dict] | None = None,
        **gen_kwargs,
    ) -> QualityResult:
        """Run the full generate -> score -> accept/reject loop.

        Args:
            generator: Callable that produces a candidate
            on_reject: Optional callback that adjusts gen_kwargs after rejection
            **gen_kwargs: Passed to generator

        Returns:
            Best QualityResult (accepted=True if passed, False if best-effort)
        """
        best_result = None
        best_composite = -1.0

        for attempt in range(1, self.max_rounds + 1):
            logger.info(f"Quality round {attempt}/{self.max_rounds}, "
                       f"generating {self.n_candidates} candidates")

            for c_idx in range(self.n_candidates):
                try:
                    candidate = generator(**gen_kwargs)
                except Exception as e:
                    logger.error(f"Generator failed on candidate {c_idx}: {e}")
                    continue

                result = self.evaluate(candidate)
                result.attempt = attempt

                if result.composite_score > best_composite:
                    best_composite = result.composite_score
                    best_result = result

                if result.accepted:
                    logger.info(
                        f"Accepted candidate (round {attempt}, #{c_idx}): "
                        f"composite={result.composite_score:.3f}"
                    )
                    return result

            # All candidates in this round failed
            logger.warning(
                f"Round {attempt}: no candidate passed. "
                f"Best composite: {best_composite:.3f}"
            )

            # Adjust generation parameters if callback provided
            if on_reject and best_result:
                adjustments = on_reject(best_result)
                gen_kwargs.update(adjustments)
                logger.info(f"Adjusted generation params: {adjustments}")

        # All rounds exhausted — return best available
        if best_result:
            best_result.accepted = False
            self._log_failure(best_result)
            logger.error(
                f"Quality gate FAILED after {self.max_rounds} rounds. "
                f"Best composite: {best_composite:.3f}, "
                f"failures: {best_result.failure_reasons}"
            )

        return best_result

    def _log_failure(self, result: QualityResult):
        """Log quality failure for post-mortem analysis."""
        if self.failure_log:
            self.failure_log.parent.mkdir(parents=True, exist_ok=True)
            with open(self.failure_log, "a") as f:
                import json
                entry = {
                    "scores": result.scores,
                    "composite": result.composite_score,
                    "failures": result.failure_reasons,
                    "attempt": result.attempt,
                }
                f.write(json.dumps(entry) + "\n")
