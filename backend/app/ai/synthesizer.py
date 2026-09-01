"""
Conclusion Synthesizer — produces a structured research conclusion from evidence.
Single LLM call with full structured input. Returns ConclusionData with citations.
"""
import logging
from dataclasses import dataclass, field

from app.ai.model import get_llm_provider, parse_json_response

logger = logging.getLogger("research_agent.ai.synthesizer")

SYSTEM_PROMPT = """You are a senior research analyst producing an evidence-based conclusion.

Rules:
- Base your conclusion ONLY on the provided findings — do not add information from your training data
- If evidence is thin or contradictory, say so explicitly and lower confidence accordingly
- Cite specific finding indices when making claims
- Acknowledge contradictions and explain them rather than ignoring them
- If insufficient evidence exists, state "The available evidence is insufficient to draw a strong conclusion"

Confidence scale:
- 0.8-1.0: Strong consistent evidence from multiple reliable sources
- 0.6-0.8: Good evidence with minor gaps or slight contradictions
- 0.4-0.6: Moderate evidence, notable contradictions or limited sources
- 0.2-0.4: Weak evidence, significant contradictions or very few sources
- 0.0-0.2: Insufficient evidence

Respond ONLY with valid JSON:
{
  "conclusion": "comprehensive evidence-based conclusion text...",
  "key_points": ["point 1", "point 2", "point 3"],
  "limitations": ["limitation 1", "limitation 2"],
  "supporting_finding_indices": [0, 1, 3],
  "contradicting_finding_indices": [2],
  "confidence": 0.75
}"""


@dataclass
class ConclusionData:
    conclusion: str
    key_points: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    supporting_finding_indices: list[int] = field(default_factory=list)
    contradicting_finding_indices: list[int] = field(default_factory=list)
    confidence: float = 0.5


class ConclusionSynthesizer:
    async def synthesize(
        self,
        question: str,
        subquestions: list,
        findings: list,
        contradictions: list,
    ) -> ConclusionData:
        if not findings:
            return ConclusionData(
                conclusion="No evidence was successfully extracted from research sources. The available evidence is insufficient to draw a conclusion.",
                key_points=["No evidence extracted"],
                limitations=["Finding extraction yielded no actionable claims", "Source material may have been insufficient or unparseable"],
                confidence=0.0,
            )

        # Build findings context
        finding_lines = []
        for i, f in enumerate(findings):
            text = f.text if hasattr(f, "text") else f.get("text", "")
            clf = f.classification if hasattr(f, "classification") else f.get("classification", "")
            conf = f.confidence if hasattr(f, "confidence") else f.get("confidence", 0.5)
            finding_lines.append(f"{i}. [{clf}, confidence={conf:.2f}] {text}")

        # Build contradictions context
        contradiction_lines = []
        for c in contradictions:
            a_idx = c.finding_a_index if hasattr(c, "finding_a_index") else c.get("finding_a_index", 0)
            b_idx = c.finding_b_index if hasattr(c, "finding_b_index") else c.get("finding_b_index", 1)
            desc = c.description if hasattr(c, "description") else c.get("description", "")
            sev = c.severity if hasattr(c, "severity") else c.get("severity", "medium")
            contradiction_lines.append(f"- Findings {a_idx} vs {b_idx} ({sev} severity): {desc}")

        subq_lines = []
        for sq in subquestions:
            q = sq.question if hasattr(sq, "question") else sq.get("question", "")
            subq_lines.append(f"- {q}")

        prompt = (
            f"Main research question: {question}\n\n"
            f"Sub-questions explored:\n" + "\n".join(subq_lines) + "\n\n"
            f"Research findings ({len(findings)} total):\n" + "\n".join(finding_lines) + "\n\n"
            + (f"Detected contradictions:\n" + "\n".join(contradiction_lines) + "\n\n" if contradiction_lines else "No significant contradictions detected.\n\n")
            + "Synthesize a comprehensive, evidence-based conclusion. Reference specific finding indices where relevant."
        )

        try:
            llm = get_llm_provider()
            raw = await llm.generate(prompt, system=SYSTEM_PROMPT, json_mode=True)
            data = parse_json_response(raw)
        except Exception as exc:
            logger.error("Synthesizer LLM failed: %s", exc)
            data = {}

        if not data or not data.get("conclusion"):
            return ConclusionData(
                conclusion="The research pipeline completed but could not generate a structured conclusion due to a technical error.",
                key_points=[f.text if hasattr(f, "text") else f.get("text", "") for f in findings[:3]],
                limitations=["Conclusion generation encountered an error"],
                confidence=0.2,
            )

        def safe_int_list(lst) -> list[int]:
            result = []
            for x in (lst or []):
                try:
                    idx = int(x)
                    if 0 <= idx < len(findings):
                        result.append(idx)
                except (TypeError, ValueError):
                    pass
            return result

        return ConclusionData(
            conclusion=str(data.get("conclusion", "")),
            key_points=[str(p) for p in data.get("key_points", []) if p],
            limitations=[str(l) for l in data.get("limitations", []) if l],
            supporting_finding_indices=safe_int_list(data.get("supporting_finding_indices", [])),
            contradicting_finding_indices=safe_int_list(data.get("contradicting_finding_indices", [])),
            confidence=max(0.0, min(1.0, float(data.get("confidence", 0.5)))),
        )
