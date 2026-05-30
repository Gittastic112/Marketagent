from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import create_record, delete_record, get_or_404, update_record
from app.api.schemas import (
    ApiResponse,
    SocialPostCreate, SocialPostRead, SocialPostUpdate,
    SentimentScoreCreate, SentimentScoreRead, SentimentScoreUpdate,
    NarrativeClusterCreate, NarrativeClusterRead, NarrativeClusterUpdate,
    NarrativeClaimCreate, NarrativeClaimRead, NarrativeClaimUpdate,
    NarrativeMentionCreate, NarrativeMentionRead, NarrativeMentionUpdate
)
from app.db.session import get_db
from app.models.social import SocialPost, SentimentScore, NarrativeCluster, NarrativeClaim, NarrativeMention

import hashlib

router = APIRouter(tags=["social"])

@router.post("/social-posts", response_model=ApiResponse[SocialPostRead], status_code=status.HTTP_201_CREATED)
def create_social_post(payload: SocialPostCreate, db: Session = Depends(get_db)) -> SocialPost:
    post = SocialPost(**payload.model_dump())
    if not post.content_hash:
        content = f"{post.platform}:{post.source_url}:{post.raw_text}"
        post.content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    db.add(post)
    db.commit()
    db.refresh(post)
    return ApiResponse(data=post)

@router.get("/social-posts", response_model=ApiResponse[list[SocialPostRead]])
def list_social_posts(db: Session = Depends(get_db)) -> list[SocialPost]:
    return ApiResponse(data=list(db.scalars(select(SocialPost).order_by(SocialPost.created_at.desc()))))

@router.get("/social-posts/{post_id}", response_model=ApiResponse[SocialPostRead])
def get_social_post(post_id: int, db: Session = Depends(get_db)) -> SocialPost:
    return ApiResponse(data=get_or_404(db, SocialPost, post_id))

@router.patch("/social-posts/{post_id}", response_model=ApiResponse[SocialPostRead])
def update_social_post(post_id: int, payload: SocialPostUpdate, db: Session = Depends(get_db)) -> SocialPost:
    return ApiResponse(data=update_record(db, get_or_404(db, SocialPost, post_id), payload))

@router.delete("/social-posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_social_post(post_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, SocialPost, post_id))

# Sentiment Scores
@router.post("/sentiment-scores", response_model=ApiResponse[SentimentScoreRead], status_code=status.HTTP_201_CREATED)
def create_sentiment_score(payload: SentimentScoreCreate, db: Session = Depends(get_db)) -> SentimentScore:
    return ApiResponse(data=create_record(db, SentimentScore, payload))

@router.get("/sentiment-scores", response_model=ApiResponse[list[SentimentScoreRead]])
def list_sentiment_scores(db: Session = Depends(get_db)) -> list[SentimentScore]:
    return ApiResponse(data=list(db.scalars(select(SentimentScore).order_by(SentimentScore.created_at.desc()))))

@router.get("/sentiment-scores/{score_id}", response_model=ApiResponse[SentimentScoreRead])
def get_sentiment_score(score_id: int, db: Session = Depends(get_db)) -> SentimentScore:
    return ApiResponse(data=get_or_404(db, SentimentScore, score_id))

@router.patch("/sentiment-scores/{score_id}", response_model=ApiResponse[SentimentScoreRead])
def update_sentiment_score(score_id: int, payload: SentimentScoreUpdate, db: Session = Depends(get_db)) -> SentimentScore:
    return ApiResponse(data=update_record(db, get_or_404(db, SentimentScore, score_id), payload))

@router.delete("/sentiment-scores/{score_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sentiment_score(score_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, SentimentScore, score_id))

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
def create_narrative_claim(payload: NarrativeClaimCreate, db: Session = Depends(get_db)) -> NarrativeClaim:
    return ApiResponse(data=create_record(db, NarrativeClaim, payload))

@router.get("/narrative-claims", response_model=ApiResponse[list[NarrativeClaimRead]])
def list_narrative_claims(cluster_id: int | None = None, db: Session = Depends(get_db)) -> list[NarrativeClaim]:
    query = select(NarrativeClaim).order_by(NarrativeClaim.created_at.desc())
    if cluster_id:
        query = query.where(NarrativeClaim.cluster_id == cluster_id)
    return ApiResponse(data=list(db.scalars(query)))

@router.get("/narrative-claims/{claim_id}", response_model=ApiResponse[NarrativeClaimRead])
def get_narrative_claim(claim_id: int, db: Session = Depends(get_db)) -> NarrativeClaim:
    return ApiResponse(data=get_or_404(db, NarrativeClaim, claim_id))

@router.patch("/narrative-claims/{claim_id}", response_model=ApiResponse[NarrativeClaimRead])
def update_narrative_claim(claim_id: int, payload: NarrativeClaimUpdate, db: Session = Depends(get_db)) -> NarrativeClaim:
    return ApiResponse(data=update_record(db, get_or_404(db, NarrativeClaim, claim_id), payload))

@router.delete("/narrative-claims/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_narrative_claim(claim_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, NarrativeClaim, claim_id))

# Narrative Mentions
@router.post("/narrative-mentions", response_model=ApiResponse[NarrativeMentionRead], status_code=status.HTTP_201_CREATED)
def create_narrative_mention(payload: NarrativeMentionCreate, db: Session = Depends(get_db)) -> NarrativeMention:
    return ApiResponse(data=create_record(db, NarrativeMention, payload))

@router.get("/narrative-mentions", response_model=ApiResponse[list[NarrativeMentionRead]])
def list_narrative_mentions(cluster_id: int | None = None, post_id: int | None = None, db: Session = Depends(get_db)) -> list[NarrativeMention]:
    query = select(NarrativeMention).order_by(NarrativeMention.created_at.desc())
    if cluster_id:
        query = query.where(NarrativeMention.cluster_id == cluster_id)
    if post_id:
        query = query.where(NarrativeMention.post_id == post_id)
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
