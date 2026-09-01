"""
Question Decomposer — turns a research question into structured sub-questions.
Single LLM call. Returns 3-5 SubQuestion dicts.
"""
import json
import logging
from dataclasses import dataclass

from app.ai.model import get_llm_provider, parse_json_response

logger = logging.getLogger("research_agent.ai.decomposer")

SYSTEM_PROMPT = """You are an expert research analyst. Your task is to decompose a broad research question into 3-5 focused sub-questions that will guide comprehensive research.

Each sub-question should:
- Be specific and answerable through web research
- Cover a different aspect of the main question
- Have a clear research intent explaining WHY this sub-question matters

Respond ONLY with valid JSON in exactly this format:
{"subquestions": [{"id": "sq1", "question": "...", "research_intent": "..."}, ...]}"""


@dataclass
class SubQuestionData:
    id: str
    question: str
    research_intent: str


class QuestionDecomposer:
    async def decompose(self, question: str) -> list[SubQuestionData]:
        llm = get_llm_provider()
        prompt = (
            f"Research question: {question}\n\n"
            "Decompose this into 3-5 focused sub-questions for systematic research. "
            "Cover: current state/adoption, technologies/methods, benefits/opportunities, "
            "challenges/risks, and future directions."
        )

        try:
            raw = await llm.generate(prompt, system=SYSTEM_PROMPT, json_mode=True)
            data = parse_json_response(raw)
            subqs = data.get("subquestions", []) if isinstance(data, dict) else []
        except Exception as exc:
            logger.error("Decomposition LLM call failed: %s", exc)
            subqs = []

        if not subqs:
            # Deterministic fallback — always return something useful
            logger.warning("Using fallback decomposition for: %s", question)
            subqs = [
                {"id": "sq1", "question": f"What is the current state of AI adoption in: {question}?", "research_intent": "Understand baseline"},
                {"id": "sq2", "question": f"What AI technologies are most commonly used for: {question}?", "research_intent": "Identify key technologies"},
                {"id": "sq3", "question": f"What are the documented benefits of AI for: {question}?", "research_intent": "Quantify benefits"},
                {"id": "sq4", "question": f"What risks or challenges exist for AI in: {question}?", "research_intent": "Identify barriers"},
            ]

        result = []
        for i, sq in enumerate(subqs[:5]):  # Cap at 5
            result.append(SubQuestionData(
                id=sq.get("id", f"sq{i+1}"),
                question=sq.get("question", ""),
                research_intent=sq.get("research_intent", ""),
            ))

        return [r for r in result if r.question]  # Filter empty
