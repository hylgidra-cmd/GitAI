"""Content workflow: draft -> in_review -> published (two-step, role-gated)."""
from fastapi import HTTPException

from app.models import ContentStatus, PlaceContent, Role

# (from, to) -> roles allowed
TRANSITIONS: dict[tuple[ContentStatus, ContentStatus], set[Role]] = {
    (ContentStatus.draft, ContentStatus.in_review): {Role.content_manager, Role.editor, Role.admin},
    (ContentStatus.in_review, ContentStatus.published): {Role.editor, Role.admin},
    (ContentStatus.in_review, ContentStatus.draft): {Role.editor, Role.admin},
    (ContentStatus.published, ContentStatus.draft): {Role.admin},
}


def validate_publishable(content: PlaceContent) -> None:
    if not content.body.strip() or not content.title.strip():
        raise HTTPException(422, "content_empty")
    refs = content.source_refs or []
    if not refs or any(not r.get("license") for r in refs):
        raise HTTPException(422, "source_license_required")


def transition(content: PlaceContent, target: ContentStatus, role: Role) -> None:
    allowed = TRANSITIONS.get((content.status, target))
    if allowed is None:
        raise HTTPException(409, f"invalid_transition:{content.status.value}->{target.value}")
    if role not in allowed:
        raise HTTPException(403, "forbidden_transition")
    if target == ContentStatus.published:
        validate_publishable(content)
    content.status = target
