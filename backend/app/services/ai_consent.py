"""Append-only permissions for explicit external AI actions. Reads never grant."""
from dataclasses import dataclass
from datetime import UTC
import hashlib
import json
import os

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.ai_consent import AiConsentDecision
from app.schemas.ai_consent import (
    AIConsentActionRead, AIConsentDecisionRead, AIConsentDecisionRequest,
    AIConsentHistory, AIConsentOverview,
)


@dataclass(frozen=True)
class ConsentAction:
    key: str
    label: str
    description: str
    data_classes: tuple[str, ...]


# These are the available application actions, not inferred prompt prefixes.
# Dormant contradiction helpers are deliberately absent and cannot acquire grants.
ACTIONS = (
    ConsentAction("document_summary", "Document summary", "Selected document text or its title when text is unavailable.", ("raw_document_text",)),
    ConsentAction("research_summary", "Evidence summary", "Selected document text and the task you enter.", ("raw_document_text", "user_task")),
    ConsentAction("research_question", "Evidence question", "Selected document text and the question you enter.", ("raw_document_text", "user_question")),
    ConsentAction("event_mapping", "Event DCF interpretation", "Selected event title and description. No saved valuation values or thesis assumptions.", ("event_text",)),
    ConsentAction("narrative_to_numbers", "Narrative estimates", "Your narrative, current saved valuation assumptions and saved-version identifiers, dates, currency and output hash.", ("user_narrative", "valuation_assumptions", "valuation_version_metadata")),
    ConsentAction("valuation_memo", "Valuation memo", "Company identity, saved valuation name/type/scenario/version, assumptions and story text, calculated outputs and diagnostics.", ("company_metadata", "valuation_metadata", "valuation_assumptions", "valuation_outputs")),
    ConsentAction("narrative_extraction", "Event narratives", "Event titles and descriptions, sent separately for each selected event.", ("event_text",)),
    ConsentAction("thesis_impact", "Thesis impact", "Event title/description and your active thesis assumptions, including descriptions, categories, identifiers and falsification triggers.", ("event_text", "private_thesis_assumptions")),
    ConsentAction("private_source_scan", "Private source scan", "Selected source text, source date, company name/ticker and a valuation field-name catalog. No stored holdings, thesis notes or valuation values.", ("selected_source_text", "source_date", "public_company_identity", "valuation_field_names")),
    ConsentAction("research_chat", "Research chat", "All messages in the selected private research session, plus titles and bounded excerpts of up to three retrieved documents when available.", ("private_research_messages", "retrieved_document_excerpts")),
)
ACTION_BY_KEY = {action.key: action for action in ACTIONS}
PROVIDER = "gemini"


class ConsentPolicyError(ValueError):
    def __init__(self, code: str, message: str, status_code: int = 409):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def disclosure_version() -> str:
    return os.environ.get("AI_PRIVACY_DISCLOSURE_VERSION", "v1")


def action_scope_hash(action: ConsentAction) -> str:
    payload = {"provider": PROVIDER, "action": action.key, "description": action.description,
               "data_classes": sorted(action.data_classes), "disclosure_version": disclosure_version()}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def latest_decision(db: Session, user_id: str, provider_name: str, action_key: str) -> AiConsentDecision | None:
    # Refresh ORM identity state so a revocation in another request is not cached.
    return db.scalar(select(AiConsentDecision).where(
        AiConsentDecision.user_id == user_id, AiConsentDecision.provider_name == provider_name,
        AiConsentDecision.action_key == action_key,
    ).order_by(AiConsentDecision.revision.desc()).limit(1).execution_options(populate_existing=True))


def decision_read(row: AiConsentDecision) -> AIConsentDecisionRead:
    created = row.created_at.replace(tzinfo=UTC) if row.created_at.tzinfo is None else row.created_at
    return AIConsentDecisionRead(id=row.id, provider_name=row.provider_name, action_key=row.action_key,
        revision=row.revision, state=row.state, disclosure_version=row.disclosure_version,
        scope_hash=row.scope_hash, external_data_classes=list(row.external_data_classes_json), created_at=created)


def is_current(row: AiConsentDecision, action: ConsentAction) -> bool:
    return (row.disclosure_version == disclosure_version() and row.scope_hash == action_scope_hash(action)
            and sorted(row.external_data_classes_json) == sorted(action.data_classes))


def consent_overview(db: Session, user_id: str) -> AIConsentOverview:
    items = []
    for action in ACTIONS:
        latest = latest_decision(db, user_id, PROVIDER, action.key)
        state = "not_granted" if latest is None else latest.state if is_current(latest, action) else "outdated"
        items.append(AIConsentActionRead(provider_name=PROVIDER, action_key=action.key, label=action.label,
            description=action.description, external_data_classes=list(action.data_classes),
            disclosure_version=disclosure_version(), scope_hash=action_scope_hash(action), state=state,
            current_revision=latest.revision if latest else 0,
            latest_decision=decision_read(latest) if latest else None))
    return AIConsentOverview(actions=items, limitations=[
        "Permissions allow only the named action and listed data scope with Gemini. Provider setup is separate.",
        "Each action still requires its own disclosure acknowledgement. Reading this page grants nothing.",
        "Refusal and revocation block subsequent sends. They cannot recall data already sent or cancel a request already dispatched.",
        "Mock Data generation stays local and never creates a permission. The operator-only fixed-text connection check sends no application records.",
    ])


def record_decision(db: Session, user_id: str, request: AIConsentDecisionRequest) -> AiConsentDecision:
    action = ACTION_BY_KEY.get(request.action_key)
    if request.provider_name != PROVIDER or action is None:
        raise ConsentPolicyError("AI_CONSENT_SCOPE_UNAVAILABLE", "This AI permission scope is not available.", 422)
    if request.disclosure_version != disclosure_version() or request.scope_hash != action_scope_hash(action):
        raise ConsentPolicyError("AI_CONSENT_SCOPE_CHANGED", "The AI disclosure changed. Reload permissions and review the current scope.")
    previous = latest_decision(db, user_id, request.provider_name, request.action_key)
    revision = previous.revision if previous else 0
    if revision != request.expected_revision:
        raise ConsentPolicyError("AI_CONSENT_CONFLICT", "This permission changed in another request. Reload before deciding again.")
    row = AiConsentDecision(user_id=user_id, provider_name=PROVIDER, action_key=action.key,
        revision=revision + 1, state=request.state, disclosure_version=disclosure_version(),
        scope_hash=action_scope_hash(action), external_data_classes_json=list(action.data_classes))
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # The unique owner/provider/action/revision constraint closes simultaneous-write races.
        raise ConsentPolicyError("AI_CONSENT_CONFLICT", "This permission changed in another request. Reload before deciding again.") from None
    db.refresh(row)
    return row


def consent_history(db: Session, user_id: str, *, cursor: int | None = None, limit: int = 25) -> AIConsentHistory:
    query = select(AiConsentDecision).where(AiConsentDecision.user_id == user_id)
    if cursor is not None:
        query = query.where(AiConsentDecision.id < cursor)
    rows = list(db.scalars(query.order_by(AiConsentDecision.id.desc()).limit(limit + 1)))
    page = rows[:limit]
    return AIConsentHistory(items=[decision_read(row) for row in page],
                           next_cursor=page[-1].id if len(rows) > limit else None)


def authorize_external_call(db: Session, *, user_id: str, provider_name: str, action_key: str | None,
                            acknowledgement: str | None, data_classes: tuple[str, ...]) -> AiConsentDecision:
    action = ACTION_BY_KEY.get(action_key or "")
    if provider_name != PROVIDER or action is None:
        raise ConsentPolicyError("AI_CONSENT_SCOPE_UNAVAILABLE", "This external AI action is not available under the current permission policy.")
    if acknowledgement != disclosure_version():
        raise ConsentPolicyError("AI_PRIVACY_DISCLOSURE_REQUIRED", "Review and acknowledge the current AI data disclosure before continuing.")
    # A payload can omit optional retrieved excerpts, but may never exceed the granted scope.
    declared, allowed = set(data_classes), set(action.data_classes)
    matches = (declared <= allowed and "private_research_messages" in declared
               if action.key == "research_chat" else declared == allowed)
    if not matches or len(declared) != len(data_classes):
        raise ConsentPolicyError("AI_CONSENT_SCOPE_CHANGED", "The AI request does not match its disclosed data scope. No provider request was sent.")
    decision = latest_decision(db, user_id, provider_name, action.key)
    if decision is None or decision.state != "granted" or not is_current(decision, action):
        raise ConsentPolicyError("AI_CONSENT_REQUIRED", "No current permission allows this AI action. Review AI permissions in Settings before trying again.")
    return decision
