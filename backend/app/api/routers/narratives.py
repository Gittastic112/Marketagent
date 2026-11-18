from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import create_record, delete_record, get_or_404, update_record
from app.api.schemas import (
    AIPrivacyAcknowledgement,
    ApiResponse,
    NarrativeClusterCreate, NarrativeClusterRead, NarrativeClusterUpdate,
    NarrativeClaimCreate, NarrativeClaimRead, NarrativeClaimUpdate,
    NarrativeMentionCreate, NarrativeMentionRead, NarrativeMentionUpdate
)
from app.api.ai_errors import public_ai_error
from app.api.dependencies import get_current_user
from app.services.ai_contract import AIExecutionError, require_privacy_disclosure
from app.services.narrative_origin import claims_with_origin
from app.db.session import get_db
from app.models.narrative import NarrativeCluster, NarrativeClaim, NarrativeMention

router = APIRouter(tags=["narratives"])

# Narrative Clusters
@router.post("/narrative-clusters", response_model=ApiResponse[NarrativeClusterRead], status_code=status.HTTP_201_CREATED)
def create_narrative_cluster(payload: NarrativeClusterCreate, db: Session = Depends(get_db)) -> NarrativeCluster:
    return ApiResponse(data=create_record(db, NarrativeCluster, payload))

@router.get("/narrative-clusters", response_model=ApiResponse[list[NarrativeClusterRead]])
def list_narrative_clusters(db: Session = Depends(get_db)) -> list[NarrativeCluster]:
    return ApiResponse(data=list(db.scalars(select(NarrativeCluster).order_by(NarrativeCluster.created_at.desc()))))

@router.get("/narrative-clusters/{cluster_id}", response_model=ApiResponse[NarrativeClusterRead])
def get_narrative_cluster(cluster_id: int, db: Session = Depends(get_db)) -> NarrativeCluster:
    return ApiResponse(data=get_or_404(db, NarrativeCluster, cluster_id))

@router.patch("/narrative-clusters/{cluster_id}", response_model=ApiResponse[NarrativeClusterRead])
def update_narrative_cluster(cluster_id: int, payload: NarrativeClusterUpdate, db: Session = Depends(get_db)) -> NarrativeCluster:
    return ApiResponse(data=update_record(db, get_or_404(db, NarrativeCluster, cluster_id), payload))

@router.delete("/narrative-clusters/{cluster_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_narrative_cluster(cluster_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, NarrativeCluster, cluster_id))

# Narrative Claims
@router.post("/narrative-claims", response_model=ApiResponse[NarrativeClaimRead], status_code=status.HTTP_201_CREATED)
def create_narrative_claim(payload: NarrativeClaimCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    get_or_404(db, NarrativeCluster, payload.cluster_id)
    claim = NarrativeClaim(**payload.model_dump(), origin="manual")
    db.add(claim); db.commit(); db.refresh(claim)
    return ApiResponse(data=claims_with_origin(db, [claim], current_user["id"])[0])

@router.get("/narrative-claims", response_model=ApiResponse[list[NarrativeClaimRead]])
def list_narrative_claims(cluster_id: int | None = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    query = select(NarrativeClaim).order_by(NarrativeClaim.created_at.desc())
    if cluster_id:
        query = query.where(NarrativeClaim.cluster_id == cluster_id)
    return ApiResponse(data=claims_with_origin(db, list(db.scalars(query)), current_user["id"]))

@router.get("/narrative-claims/{claim_id}", response_model=ApiResponse[NarrativeClaimRead])
def get_narrative_claim(claim_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return ApiResponse(data=claims_with_origin(db, [get_or_404(db, NarrativeClaim, claim_id)], current_user["id"])[0])

@router.patch("/narrative-claims/{claim_id}", response_model=ApiResponse[NarrativeClaimRead])
def update_narrative_claim(claim_id: int, payload: NarrativeClaimUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    claim = get_or_404(db, NarrativeClaim, claim_id)
    if claim.ai_output_id is not None:
        raise HTTPException(status_code=409, detail="Generated claims retain their original evidence. Add a separate manual claim to record a correction.")
    return ApiResponse(data=claims_with_origin(db, [update_record(db, claim, payload)], current_user["id"])[0])

@router.delete("/narrative-claims/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_narrative_claim(claim_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, NarrativeClaim, claim_id))

# Narrative Mentions
@router.post("/narrative-mentions", response_model=ApiResponse[NarrativeMentionRead], status_code=status.HTTP_201_CREATED)
def create_narrative_mention(payload: NarrativeMentionCreate, db: Session = Depends(get_db)) -> NarrativeMention:
    return ApiResponse(data=create_record(db, NarrativeMention, payload))

@router.get("/narrative-mentions", response_model=ApiResponse[list[NarrativeMentionRead]])
def list_narrative_mentions(cluster_id: int | None = None, event_id: int | None = None, db: Session = Depends(get_db)) -> list[NarrativeMention]:
    query = select(NarrativeMention).order_by(NarrativeMention.created_at.desc())
    if cluster_id:
        query = query.where(NarrativeMention.cluster_id == cluster_id)
    if event_id:
        query = query.where(NarrativeMention.event_id == event_id)
    return ApiResponse(data=list(db.scalars(query)))

@router.get("/narrative-mentions/{mention_id}", response_model=ApiResponse[NarrativeMentionRead])
def get_narrative_mention(mention_id: int, db: Session = Depends(get_db)) -> NarrativeMention:
    return ApiResponse(data=get_or_404(db, NarrativeMention, mention_id))

@router.patch("/narrative-mentions/{mention_id}", response_model=ApiResponse[NarrativeMentionRead])
def update_narrative_mention(mention_id: int, payload: NarrativeMentionUpdate, db: Session = Depends(get_db)) -> NarrativeMention:
    return ApiResponse(data=update_record(db, get_or_404(db, NarrativeMention, mention_id), payload))

@router.delete("/narrative-mentions/{mention_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_narrative_mention(mention_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, NarrativeMention, mention_id))

# Narrative Extraction
@router.post("/extract", response_model=ApiResponse[dict], status_code=status.HTTP_200_OK)
def extract_narratives(
    acknowledgement: AIPrivacyAcknowledgement,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    from app.services.narrative_extraction import extract_narratives_from_events
    try:
        require_privacy_disclosure(acknowledgement.privacy_disclosure_version)
        result = extract_narratives_from_events(
            db,
            user_id=current_user["id"],
            limit=limit,
            privacy_disclosure_version=acknowledgement.privacy_disclosure_version,
        )
    except AIExecutionError as exc:
        raise public_ai_error(exc) from exc
    return ApiResponse(
        data={
            "created_clusters": result.created_clusters,
            "created_claims": result.created_claims,
            "created_mentions": result.created_mentions,
            "skipped_existing": result.skipped_existing,
        }
    )
