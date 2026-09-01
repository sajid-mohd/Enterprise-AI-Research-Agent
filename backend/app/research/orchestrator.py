"""
Research Orchestrator — coordinates the full research pipeline.
Runs as a background task. Updates session status after each step.
Persists partial results so the frontend can show live progress.
"""
import asyncio
import logging
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.ai.decomposer import QuestionDecomposer
from app.ai.extractor import FindingExtractor
from app.ai.contradiction import ContradictionDetector
from app.ai.synthesizer import ConclusionSynthesizer
from app.models.research_session import ResearchSession
from app.models.sub_question import SubQuestion
from app.models.source import Source
from app.models.finding import Finding
from app.models.contradiction import Contradiction
from app.models.conclusion import Conclusion, ConclusionFinding
from app.research.search import MultiSearchProvider
from app.research.scraper import Scraper
from app.research.cleaner import clean_html, compute_word_count, extract_domain, estimate_reliability
from app.storage.vector_store import VectorStore
from app.core.config import settings

logger = logging.getLogger("research_agent.orchestrator")


def _set_status(db: Session, session: ResearchSession, status: str, error: str = None):
    session.status = status
    session.updated_at = datetime.utcnow()
    if error:
        session.error_message = error
    db.commit()
    logger.info("Session %s → %s %s", session.id, status, f"({error})" if error else "")


class ResearchOrchestrator:
    def __init__(self):
        self.decomposer = QuestionDecomposer()
        self.extractor = FindingExtractor()
        self.contradiction_detector = ContradictionDetector()
        self.synthesizer = ConclusionSynthesizer()
        self.search_provider = MultiSearchProvider()
        self.scraper = Scraper()
        self.vector_store = VectorStore()

    async def run(self, session_id: str, db: Session) -> None:
        """Full pipeline. Called as a background task."""
        try:
            session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
            if not session:
                logger.error("Session %s not found", session_id)
                return

            question = session.question
            logger.info("Starting research for session %s: %s", session_id, question[:80])

            # ── Step 1: Decompose question ──────────────────────────────────────
            _set_status(db, session, "decomposing")
            try:
                subquestion_data = await self.decomposer.decompose(question)
            except Exception as exc:
                _set_status(db, session, "failed", f"Decomposition failed: {exc}")
                return

            if not subquestion_data:
                _set_status(db, session, "failed", "Question decomposition produced no sub-questions.")
                return

            # Persist sub-questions
            db_subquestions: list[SubQuestion] = []
            for sq in subquestion_data[:settings.MAX_SUBQUESTIONS]:
                db_sq = SubQuestion(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    question=sq.question,
                    research_intent=sq.research_intent,
                    status="pending",
                )
                db.add(db_sq)
                db_subquestions.append(db_sq)
            db.commit()

            logger.info("Decomposed into %d sub-questions", len(db_subquestions))

            # ── Step 2: Search + Scrape + Store sources ─────────────────────────
            _set_status(db, session, "searching")
            db_sources: list[Source] = []

            for db_sq in db_subquestions:
                db_sq.status = "searching"
                db.commit()

                try:
                    search_results = await asyncio.get_running_loop().run_in_executor(
                        None, self.search_provider.search, db_sq.question
                    )
                except Exception as exc:
                    logger.warning("Search failed for sub-question %s: %s", db_sq.id, exc)
                    search_results = []

                seen_urls: set[str] = set()
                for result in search_results[:settings.MAX_SOURCES_PER_SUBQUESTION]:
                    url = result.get("url", "").strip()
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    # Scrape
                    raw_html = await self.scraper.fetch(url)
                    if not raw_html and result.get("source_type") == "wikipedia":
                        raw_html = result.get("snippet", "")  # Use snippet for Wikipedia

                    if not raw_html:
                        continue

                    cleaned = clean_html(raw_html)
                    if not cleaned or len(cleaned.strip()) < 80:
                        continue

                    domain = extract_domain(url)
                    word_count = compute_word_count(cleaned)
                    reliability = estimate_reliability(domain, result.get("source_type", "web"), word_count)

                    db_source = Source(
                        id=str(uuid.uuid4()),
                        sub_question_id=db_sq.id,
                        url=url,
                        title=result.get("title", domain)[:500],
                        domain=domain,
                        source_type=result.get("source_type", "web"),
                        retrieved_at=datetime.utcnow(),
                        raw_content=raw_html[:50000],  # Cap raw to 50k chars
                        cleaned_content=cleaned,
                        word_count=word_count,
                        reliability_score=reliability,
                    )
                    db.add(db_source)
                    db_sources.append(db_source)

                db_sq.status = "completed"
                db.commit()

            logger.info("Collected %d usable sources total", len(db_sources))

            if not db_sources:
                _set_status(db, session, "failed", "No usable sources could be retrieved from search.")
                return

            # ── Step 3: Extract findings ────────────────────────────────────────
            _set_status(db, session, "extracting")

            # Build a map from source_id → parent subquestion question text
            sq_by_id = {sq.id: sq for sq in db_subquestions}
            source_to_sq: dict[str, SubQuestion] = {}
            for src in db_sources:
                source_to_sq[src.id] = sq_by_id.get(src.sub_question_id)

            all_findings_data: list = []
            all_db_findings: list[Finding] = []
            last_extraction_error = None
            extraction_attempt_count = 0

            for db_source in db_sources:
                sq = source_to_sq.get(db_source.id)
                sq_question = sq.question if sq else question
                extraction_attempt_count += 1

                try:
                    findings_data = await self.extractor.extract(
                        source_content=db_source.cleaned_content,
                        subquestion=sq_question,
                        source_url=db_source.url,
                    )
                except Exception as exc:
                    last_extraction_error = str(exc)
                    logger.warning("Extraction failed for source %s: %s", db_source.url, exc)
                    findings_data = []

                for fd in findings_data:
                    db_finding = Finding(
                        id=str(uuid.uuid4()),
                        source_id=db_source.id,
                        text=fd.text,
                        classification=fd.classification,
                        confidence=fd.confidence,
                    )
                    db.add(db_finding)
                    all_db_findings.append(db_finding)
                    all_findings_data.append(fd)

                    # Embed in ChromaDB for semantic search
                    try:
                        self.vector_store.add_finding(
                            finding_id=db_finding.id,
                            text=fd.text,
                            metadata={
                                "session_id": session_id,
                                "source_id": db_source.id,
                                "source_url": db_source.url,
                                "classification": fd.classification,
                                "confidence": str(fd.confidence),
                            },
                        )
                    except Exception as exc:
                        logger.warning("ChromaDB embedding failed: %s", exc)

            db.commit()
            logger.info("Extracted %d findings from %d sources", len(all_db_findings), len(db_sources))

            if not all_db_findings:
                err_msg = f"Collected {len(db_sources)} sources, but finding extraction failed."
                if last_extraction_error:
                    err_msg += f" LLM error: {last_extraction_error}"
                _set_status(db, session, "failed", err_msg)
                return

            # ── Step 4: Detect contradictions ───────────────────────────────────
            _set_status(db, session, "analyzing")

            # Cap findings for analysis to prevent LLM context explosion
            MAX_FINDINGS_FOR_ANALYSIS = 40
            findings_for_analysis = all_findings_data[:MAX_FINDINGS_FOR_ANALYSIS]
            db_findings_for_analysis = all_db_findings[:MAX_FINDINGS_FOR_ANALYSIS]

            contradiction_data = []
            if len(findings_for_analysis) >= 2:
                try:
                    contradiction_data = await self.contradiction_detector.detect(findings_for_analysis)
                except Exception as exc:
                    logger.warning("Contradiction detection failed: %s", exc)
                    contradiction_data = []

            for cd in contradiction_data:
                try:
                    finding_a = db_findings_for_analysis[cd.finding_a_index]
                    finding_b = db_findings_for_analysis[cd.finding_b_index]
                    db_contradiction = Contradiction(
                        id=str(uuid.uuid4()),
                        finding_a_id=finding_a.id,
                        finding_b_id=finding_b.id,
                        description=cd.description,
                        severity=cd.severity,
                        confidence=cd.confidence,
                    )
                    db.add(db_contradiction)
                except IndexError:
                    logger.warning("Contradiction index out of range, skipping")

            db.commit()
            logger.info("Detected %d contradictions", len(contradiction_data))

            # ── Step 5: Synthesize conclusion ───────────────────────────────────
            _set_status(db, session, "synthesizing")

            try:
                conclusion_data = await self.synthesizer.synthesize(
                    question=question,
                    subquestions=db_subquestions,
                    findings=findings_for_analysis,
                    contradictions=contradiction_data,
                )
            except Exception as exc:
                logger.error("Synthesis failed: %s", exc)
                _set_status(db, session, "failed", f"Conclusion synthesis failed: {exc}")
                return

            import json
            db_conclusion = Conclusion(
                id=str(uuid.uuid4()),
                session_id=session_id,
                text=conclusion_data.conclusion,
                confidence=conclusion_data.confidence,
                key_points=json.dumps(conclusion_data.key_points),
                limitations=json.dumps(conclusion_data.limitations),
            )
            db.add(db_conclusion)
            db.flush()  # Get conclusion ID before adding links

            # Link conclusion to findings (traceability)
            for idx in conclusion_data.supporting_finding_indices:
                if 0 <= idx < len(db_findings_for_analysis):
                    link = ConclusionFinding(
                        conclusion_id=db_conclusion.id,
                        finding_id=db_findings_for_analysis[idx].id,
                        relationship_type="supporting",
                    )
                    db.add(link)

            for idx in conclusion_data.contradicting_finding_indices:
                if 0 <= idx < len(db_findings_for_analysis):
                    link = ConclusionFinding(
                        conclusion_id=db_conclusion.id,
                        finding_id=db_findings_for_analysis[idx].id,
                        relationship_type="contradicting",
                    )
                    db.add(link)

            db.commit()

            # ── Done ────────────────────────────────────────────────────────────
            _set_status(db, session, "completed")
            logger.info(
                "Session %s completed. Sources: %d, Findings: %d, Contradictions: %d, Confidence: %.2f",
                session_id, len(db_sources), len(all_db_findings), len(contradiction_data), conclusion_data.confidence,
            )

        except Exception as exc:
            logger.exception("Unexpected error in orchestrator for session %s: %s", session_id, exc)
            try:
                session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
                if session:
                    _set_status(db, session, "failed", f"Unexpected error: {str(exc)[:500]}")
            except Exception:
                pass
        finally:
            try:
                db.close()
            except Exception:
                pass
