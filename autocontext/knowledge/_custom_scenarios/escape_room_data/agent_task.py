"""Auto-generated agent task: escape_room_data."""
from __future__ import annotations

import yaml
from pathlib import Path

from autocontext.config import load_settings
from autocontext.execution.judge import LLMJudge
from autocontext.providers.registry import get_provider
from autocontext.scenarios.agent_task import AgentTaskInterface, AgentTaskResult


# Load spec from YAML
_spec_path = Path(__file__).parent / "spec.yaml"
with open(_spec_path) as f:
    _spec = yaml.safe_load(f)


class TemplateAgentTask(AgentTaskInterface):
    """Agent task for escape room data collection pipeline."""

    name = "escape_room_data"
    _description = _spec["description"]
    _task_prompt = _spec["task_prompt"]
    _rubric = _spec["rubric"]
    _output_format = "free_text"
    _judge_model = ""
    _max_rounds = 1
    _quality_threshold = 0.7
    _reference_context = ""
    _required_concepts = [
        "read strategy.md and playbook before acting",
        "adapt parameters based on recent run history",
        "diagnose root causes of low evidence yield",
        "run pipeline with chosen parameters",
        "update strategy.md with honest analysis",
        "commit changes",
    ]
    _pinned_dimensions = [
        "evidence_yield",
        "adaptation",
        "coverage_movement",
        "reliability",
    ]

    def get_task_prompt(self, state: dict) -> str:
        return self._task_prompt

    def evaluate_output(
        self,
        output: str,
        state: dict,
        reference_context: str | None = None,
        required_concepts: list[str] | None = None,
        calibration_examples: list[dict] | None = None,
        pinned_dimensions: list[str] | None = None,
    ) -> AgentTaskResult:
        try:
            settings = load_settings()
            provider = get_provider(settings)
            judge = LLMJudge(
                model=self._judge_model,
                rubric=self._rubric,
                provider=provider,
            )
            result = judge.evaluate(
                task_prompt=self.get_task_prompt(state),
                agent_output=output,
                reference_context=reference_context or (self._reference_context or None),
                required_concepts=required_concepts or self._required_concepts,
                calibration_examples=calibration_examples,
                pinned_dimensions=pinned_dimensions or self._pinned_dimensions,
            )
            return AgentTaskResult(
                score=result.score,
                reasoning=result.reasoning,
                dimension_scores=result.dimension_scores,
                internal_retries=result.internal_retries,
            )
        except Exception as exc:
            # Fallback heuristic judge for offline/smoke tests
            text = (output or "").lower()
            has_evidence = "evidence" in text and ("per_request" in text or "per request" in text)
            has_adaptation = "playbook" in text or "adapt" in text or "different" in text
            has_coverage = "coverage" in text or "booking" in text or "pricing" in text
            has_strategy = "strategy.md" in text
            has_commit = "commit" in text

            dim_scores = {
                "evidence_yield": 0.7 if has_evidence else 0.3,
                "adaptation": 0.8 if has_adaptation else 0.35,
                "coverage_movement": 0.7 if has_coverage else 0.4,
                "reliability": 0.8 if has_strategy and has_commit else 0.4,
            }
            weights = {
                "evidence_yield": 0.30,
                "adaptation": 0.30,
                "coverage_movement": 0.20,
                "reliability": 0.20,
            }
            score = sum(dim_scores[k] * weights[k] for k in dim_scores)
            return AgentTaskResult(
                score=score,
                reasoning=f"Fallback heuristic judge (LLM unavailable: {exc})",
                dimension_scores=dim_scores,
                internal_retries=0,
            )

    def get_rubric(self) -> str:
        return self._rubric

    def initial_state(self, seed: int | None = None) -> dict:
        return {
            "seed": seed or 0,
            "task_name": self.name,
            "template": "escape_room_data",
            "output_format": self._output_format,
        }

    def describe_task(self) -> str:
        return self._description

    def prepare_context(self, state: dict) -> dict:
        if self._reference_context:
            state["reference_context"] = self._reference_context
        return state

    def revise_output(self, output: str, judge_result: AgentTaskResult, state: dict) -> str:
        return output  # No revision for single-round tasks
