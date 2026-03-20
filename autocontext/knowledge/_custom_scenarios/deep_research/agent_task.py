"""Auto-generated agent task from template: deep_research."""
from __future__ import annotations

from autocontext.config import load_settings
from autocontext.execution.judge import LLMJudge
from autocontext.providers.registry import get_provider
from autocontext.scenarios.agent_task import AgentTaskInterface, AgentTaskResult


class TemplateAgentTask(AgentTaskInterface):
    """Agent task generated from the deep_research template."""

    name = 'deep_research'
    _description = """One-shot deep-research run for investigating a person's public online presence and first-degree connections, with rigorous state updates and source tracking."""
    _task_prompt = """You are a research agent running against this workspace:
- Research root: /Users/porter/code/research-notes/

Objective:
Investigate a person's public online presence and first-degree connections.
Prioritize genuinely new facts and verifiable links between people, organizations,
and events.

Tools available:
- `searx` (SearXNG search CLI): `searx "query" -n 10 -e google,bing`
- `scrape` (web scraper/search):
  - `scrape fetch URL --format markdown`
  - `scrape deep "query" -n 5`
  - `scrape search "query"`
  - `scrape batch URL1 URL2`
- `stealth-fetch` (Cloudflare bypass fetcher):
  - `stealth-fetch URL --format text`
  - add `--proxy` for residential proxy
- `cf-render` (Cloudflare Browser Rendering API):
  - `cf-render URL --format text --max-chars 5000`
- Headless Brave browser via OpenClaw browser tool
- `web_fetch` (basic URL fetcher)

Required workflow (execute in order):
1) Read current state:
   - leads.md
   - still-searching.md
   - known-facts.md
   - search-log.jsonl
   - meta/strategy.md

2) Plan 5-10 NEW search queries:
   - Explicitly avoid exact duplicates from search-log.jsonl.
   - Favor unexplored angles from still-searching.md and leads.md.

3) Execute research with tool escalation:
   - Start with `searx` / `scrape search` / `scrape deep` for discovery.
   - Fetch candidate URLs with `web_fetch` or `scrape fetch`.
   - If blocked/challenged, escalate to `stealth-fetch`.
   - Use `cf-render` as last resort for hard Cloudflare blocks.
   - Do not attempt automated logins.

4) Record findings:
   - Write to findings/YYYY-MM-DD.md.
   - For each finding include:
     - source URL(s)
     - what was learned
     - confidence level (high/medium/low)

5) Update state files:
   - leads.md
   - still-searching.md
   - known-facts.md

6) Update relationship graph artifacts:
   - graph.json
   - graph.html
   Add any new nodes/edges and update details for changed nodes.

7) Log every search query to search-log.jsonl.

8) Self-evaluate run quality briefly:
   - What worked
   - What failed
   - Best next leads

9) Git hygiene:
   - Create a clean commit summarizing this run.
   - Push to remote.

Output:
Return a concise free-text run report summarizing:
- queries planned/executed
- new discoveries
- state/graph updates
- dead ends
- commit hash"""
    _rubric = """Score the run from 0.0 to 1.0 using the weighted dimensions below.
Penalize rehashing known information, weak sourcing, duplicate searching,
skipped state updates, and missing query logs.

Dimensions:
1. new_discoveries (0.30)
   - Did the run uncover genuinely new facts or first-degree connections?
   - High score requires non-trivial, novel findings, not restatements.

2. source_quality (0.20)
   - Are claims backed by primary/authoritative sources (official records,
     original reporting, archived originals) rather than low-quality aggregators?

3. search_efficiency (0.20)
   - Were 5-10 purposeful queries planned and executed without duplicate waste?
   - Did the run avoid known dead-end patterns and pivot effectively?

4. tool_usage (0.15)
   - Was tooling selected appropriately per target site?
   - Did the run escalate from basic fetch to stealth-fetch/cf-render when needed,
     without overusing expensive tiers?

5. state_hygiene (0.15)
   - Were findings written with confidence + citations?
   - Were leads.md, still-searching.md, known-facts.md, graph.json, graph.html,
     and search-log.jsonl all updated correctly?
   - Was the git commit clean and meaningful?

Final score = weighted sum of these five dimensions."""
    _output_format = 'free_text'
    _judge_model = ''
    _max_rounds = 1
    _quality_threshold = 0.7
    _reference_context = """"""
    _required_concepts = ['query deduplication against search-log.jsonl', 'citation-backed findings with confidence levels', 'fetch-tier escalation strategy', 'graph updates (graph.json and graph.html)', 'state maintenance across leads/still-searching/known-facts', 'clean git commit and push']
    _calibration_examples = None
    _revision_prompt = """"""
    _sample_input = """"""
    _pinned_dimensions = ['new_discoveries', 'source_quality', 'search_efficiency', 'tool_usage', 'state_hygiene']

    def get_task_prompt(self, state: dict) -> str:
        prompt = self._task_prompt
        if self._sample_input:
            prompt += "\n\n## Input Data\n" + self._sample_input
        return prompt

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
                calibration_examples=calibration_examples or self._calibration_examples,
                pinned_dimensions=pinned_dimensions or self._pinned_dimensions,
            )
            return AgentTaskResult(
                score=result.score,
                reasoning=result.reasoning,
                dimension_scores=result.dimension_scores,
                internal_retries=result.internal_retries,
            )
        except Exception as exc:
            # Offline/auth-safe fallback so deterministic smoke tests can run without
            # external judge credentials.
            text = (output or "").lower()
            url_count = text.count("http://") + text.count("https://")
            has_queries = "query" in text
            has_confidence = "confidence" in text
            touched_state = all(k in text for k in ("leads.md", "still-searching.md", "known-facts.md"))
            touched_graph = "graph.json" in text and "graph.html" in text
            logged_queries = "search-log.jsonl" in text
            used_base_tools = ("searx" in text) or ("scrape" in text)
            used_escalation = ("stealth-fetch" in text) or ("cf-render" in text)

            dim_scores = {
                "new_discoveries": 0.8 if url_count >= 2 else 0.4,
                "source_quality": 0.8 if url_count >= 2 and has_confidence else 0.45,
                "search_efficiency": 0.75 if has_queries else 0.4,
                "tool_usage": 0.8 if used_base_tools and used_escalation else (0.6 if used_base_tools else 0.35),
                "state_hygiene": 0.85 if touched_state and touched_graph and logged_queries else 0.45,
            }
            weights = {
                "new_discoveries": 0.30,
                "source_quality": 0.20,
                "search_efficiency": 0.20,
                "tool_usage": 0.15,
                "state_hygiene": 0.15,
            }
            score = sum(dim_scores[k] * weights[k] for k in dim_scores)
            return AgentTaskResult(
                score=score,
                reasoning=(
                    "Fallback heuristic judge used because LLM judge was unavailable: "
                    f"{exc}"
                ),
                dimension_scores=dim_scores,
                internal_retries=0,
            )

    def get_rubric(self) -> str:
        return self._rubric

    def initial_state(self, seed: int | None = None) -> dict:
        state = {
            "seed": seed or 0,
            "task_name": self.name,
            "template": "deep_research",
            "output_format": self._output_format,
        }
        if self._sample_input:
            state["sample_input"] = self._sample_input
        return state

    def describe_task(self) -> str:
        return self._description

    def prepare_context(self, state: dict) -> dict:
        if self._reference_context:
            state["reference_context"] = self._reference_context
        return state

    def revise_output(
        self,
        output: str,
        judge_result: AgentTaskResult,
        state: dict,
    ) -> str:
        if not self._revision_prompt and self._max_rounds <= 1:
            return output
        settings = load_settings()
        provider = get_provider(settings)
        revision_instruction = self._revision_prompt or (
            "Revise the following output based on the judge's feedback. "
            "Maintain what works and fix what does not."
        )
        prompt = (
            f"{revision_instruction}\n\n"
            f"## Original Output\n{output}\n\n"
            f"## Judge Score: {judge_result.score:.2f}\n"
            f"## Judge Feedback\n{judge_result.reasoning}\n\n"
            f"## Task\n{self.get_task_prompt(state)}\n\n"
            "Produce an improved version:"
        )
        result = provider.complete(
            system_prompt=(
                "You are revising content based on expert feedback. Improve the output. "
                "Return only the revised content."
            ),
            user_prompt=prompt,
            model=self._judge_model,
        )
        return result.text
