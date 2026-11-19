"""Grounded RAG: hybrid (vector + lexical) retrieval over verified sources only.
If nothing relevant is found the answer is an honest refusal, never an invention."""
import math
import re
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import KnowledgeChunk, KnowledgeSource
from app.services.ai_providers import embedder, llm, tokenize

REFUSAL = {
    "en": "I don't know. Please ask a local guide.",
    "ru": "Не знаю. Пожалуйста, обратитесь к гиду.",
    "uz": "Bilmayman. Iltimos, gidga murojaat qiling.",
    "kaa": "Bilmeymen. Gidke muraját etiń.",
}


@dataclass
class Citation:
    chunk_id: str
    source_id: str
    source_title: str
    score: float


@dataclass
class Answer:
    text: str
    grounded: bool
    citations: list[Citation] = field(default_factory=list)
    cost_usd: float = 0.0


def chunk_text(text: str, max_chars: int = 600) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if cur and len(cur) + len(p) > max_chars:
            chunks.append(cur)
            cur = p
        else:
            cur = f"{cur}\n\n{p}".strip()
    if cur:
        chunks.append(cur)
    return chunks


def ingest_source(db: Session, source: KnowledgeSource, text: str) -> int:
    pieces = chunk_text(text)
    for piece in pieces:
        db.add(
            KnowledgeChunk(
                source_id=source.id,
                place_id=source.place_id,
                lang=source.lang,
                text=piece,
                embedding=embedder.embed(piece),
            )
        )
    db.flush()
    return len(pieces)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def retrieve(
    db: Session, question: str, lang: str, place_id: UUID | None, top_k: int | None = None
) -> list[tuple[KnowledgeChunk, KnowledgeSource, float]]:
    stmt = (
        select(KnowledgeChunk, KnowledgeSource)
        .join(KnowledgeSource, KnowledgeSource.id == KnowledgeChunk.source_id)
        .where(KnowledgeSource.verified.is_(True), KnowledgeChunk.lang == lang)
    )
    if place_id is not None:
        stmt = stmt.where(
            (KnowledgeChunk.place_id == place_id) | (KnowledgeChunk.place_id.is_(None))
        )
    q_vec = embedder.embed(question)
    q_tokens = set(tokenize(question))
    scored = []
    for chunk, source in db.execute(stmt).all():
        vec_score = max(0.0, _cosine(q_vec, chunk.embedding))
        c_tokens = set(tokenize(chunk.text))
        lex = len(q_tokens & c_tokens) / len(q_tokens) if q_tokens else 0.0
        scored.append((chunk, source, 0.6 * vec_score + 0.4 * lex))
    scored.sort(key=lambda x: -x[2])
    return scored[: top_k or settings.rag_top_k]


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+", text))


def answer_question(db: Session, question: str, lang: str, place_id: UUID | None) -> Answer:
    refusal = REFUSAL.get(lang, REFUSAL["en"])
    hits = retrieve(db, question, lang, place_id)
    if not hits or hits[0][2] < settings.rag_threshold:
        return Answer(text=refusal, grounded=False)
    passages = [h[0].text for h in hits]
    text, cost = llm.answer(question, passages, lang)
    # post-check: every number in the answer must appear in the passages
    if not _numbers(text) <= _numbers(" ".join(passages)):
        return Answer(text=refusal, grounded=False, cost_usd=cost)
    cites = [Citation(str(c.id), str(s.id), s.title, round(sc, 3)) for c, s, sc in hits]
    return Answer(text=text, grounded=True, citations=cites, cost_usd=cost)
