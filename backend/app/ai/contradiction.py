"""
Contradiction Detector — identifies conflicting findings across sources.
Single LLM call for all findings. Returns pairs with explanation of conflict.
"""
import logging
from dataclasses import dataclass

from app.ai.model import get_llm_provider, parse_json_response

logger = logging.getLogger("research_agent.ai.contradiction")

SYSTEM_PROMPT = """You are a critical research analyst identifying contradictions between research findings.

For each contradiction:
- Identify two findings that make conflicting or opposing claims
- Explain specifically WHY they conflict (not just "they disagree")
- Consider: Do they contradict outright, or reflect different contexts/timeframes/conditions?
- Rate severity: low (minor nuance), medium (notable disagreement), high (direct factual conflict)
- Estimate confidence that this is a genuine contradiction: 0.0-1.0

Only report genuine contradictions where claims are actually incompatible or in tension.
Do NOT report contradictions for findings about different topics.

Respond ONLY with valid JSON:
{"contradictions": [{"finding_a_index": 0, "finding_b_index": 2, "description": "explanation of conflict...", "severity": "medium", "confidence": 0.8}, ...]}"""


@dataclass
class ContradictionData:
    finding_a_index: int
    finding_b_index: int
    description: str
    severity: str = "medium"
    confidence: float = 0.7


VALID_SEVERITIES = {"low", "medium", "high"}


class ContradictionDetector:
    async def detect(self, findings: list) -> list[ContradictionData]:
        """
        findings: list of FindingData or dicts with .text attribute or ["text"] key
        Returns list of ContradictionData
        """
        if len(findings) < 2:
            return []

        # Build numbered finding list for the prompt
        finding_lines = []
        for i, f in enumerate(findings):
            text = f.text if hasattr(f, "text") else f.get("text", "")
            clf = f.classification if hasattr(f, "classification") else f.get("classification", "")
            finding_lines.append(f"{i}. [{clf}] {text}")

        findings_text = "\n".join(finding_lines)
        prompt = (
            f"Research findings ({len(findings)} total):\n{findings_text}\n\n"
            "Identify pairs of findings that contradict or conflict with each other. "
            "Use the 0-based index from the list above."
        )

        try:
            llm = get_llm_provider()
            raw = await llm.generate(prompt, system=SYSTEM_PROMPT, json_mode=True)
            data = parse_json_response(raw)
            raw_contradictions = data.get("contradictions", []) if isinstance(data, dict) else []
        except Exception as exc:
            logger.error("Contradiction detector LLM failed: %s", exc)
            return []

        results = []
        seen_pairs: set[tuple[int, int]] = set()
        max_idx = len(findings) - 1

        for c in raw_contradictions:
            try:
                a = int(c.get("finding_a_index", -1))
                b = int(c.get("finding_b_index", -1))
            except (TypeError, ValueError):
                continue

            if a < 0 or b < 0 or a > max_idx or b > max_idx or a == b:
                continue

            pair = (min(a, b), max(a, b))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            description = str(c.get("description", "")).strip()
            severity = c.get("severity", "medium")
            if severity not in VALID_SEVERITIES:
                severity = "medium"
            try:
                confidence = float(c.get("confidence", 0.7))
                confidence = max(0.0, min(1.0, confidence))
            except (TypeError, ValueError):
                confidence = 0.7

            results.append(ContradictionData(
                finding_a_index=a,
                finding_b_index=b,
                description=description,
                severity=severity,
                confidence=confidence,
            ))

        return results
