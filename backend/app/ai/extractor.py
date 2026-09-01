"""
Finding Extractor — extracts factual claims from source content.
One LLM call per source. Returns 2-5 findings with classification and confidence.
"""
import logging
from dataclasses import dataclass

from app.ai.model import get_llm_provider, parse_json_response

logger = logging.getLogger("research_agent.ai.extractor")

SYSTEM_PROMPT = """You are a research analyst extracting specific factual claims from source text.

For each finding:
- Extract a specific, concrete factual claim (not a vague summary)
- Classify as: supporting (confirms the research question topic), contradicting (challenges assumptions), emerging (new/developing trend), or uncertain (mixed/unclear evidence)
- Estimate confidence: 0.0-1.0 based on how clearly the source supports this claim

Extract 2-5 findings. Focus on claims that have evidence in the text.

Respond ONLY with valid JSON in this format:
{"findings": [{"text": "specific factual claim...", "classification": "supporting", "confidence": 0.85}, ...]}"""


@dataclass
class FindingData:
    text: str
    classification: str = "uncertain"
    confidence: float = 0.5


VALID_CLASSIFICATIONS = {"supporting", "contradicting", "emerging", "uncertain"}


class FindingExtractor:
    async def extract(
        self, source_content: str, subquestion: str, source_url: str
    ) -> list[FindingData]:
        if not source_content or len(source_content.strip()) < 80:
            logger.debug("Source content too short for %s (len=%d)", source_url, len(source_content) if source_content else 0)
            return []

        llm = get_llm_provider()
        # Truncate content to 6000 chars to stay within context limits
        content_preview = source_content[:6000]

        prompt = (
            f"Research sub-question: {subquestion}\n\n"
            f"Source URL: {source_url}\n\n"
            f"Source content:\n{content_preview}\n\n"
            "Extract 2-5 specific factual findings relevant to the sub-question above. "
            "Only extract claims clearly supported by the text."
        )

        try:
            raw = await llm.generate(prompt, system=SYSTEM_PROMPT, json_mode=True)
            data = parse_json_response(raw)

            # Handle multiple JSON formats (dict with findings/items/claims, or direct list)
            if isinstance(data, dict):
                raw_findings = (
                    data.get("findings")
                    or data.get("items")
                    or data.get("results")
                    or data.get("claims")
                    or data.get("data")
                    or []
                )
            elif isinstance(data, list):
                raw_findings = data
            else:
                raw_findings = []

        except Exception as exc:
            logger.error("Extractor LLM failed for %s: %s", source_url, exc)
            raise exc  # Propagate to caller so orchestrator can track LLM failure accurately

        results = []
        if isinstance(raw_findings, list):
            for f in raw_findings[:8]:
                if not isinstance(f, dict):
                    if isinstance(f, str) and len(f.strip()) >= 15:
                        results.append(FindingData(text=f.strip(), classification="uncertain", confidence=0.6))
                    continue

                text = str(f.get("text") or f.get("claim") or f.get("finding") or "").strip()
                if not text or len(text) < 15:
                    continue

                classification = str(f.get("classification", "uncertain")).lower().strip()
                if classification not in VALID_CLASSIFICATIONS:
                    classification = "uncertain"

                try:
                    confidence = float(f.get("confidence", 0.7))
                    confidence = max(0.0, min(1.0, confidence))
                except (TypeError, ValueError):
                    confidence = 0.7

                results.append(FindingData(text=text, classification=classification, confidence=confidence))

        logger.info("Extracted %d findings for %s", len(results), source_url)
        return results
