from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import create_record, delete_record, get_or_404, update_record
from app.api.schemas import (
    ApiResponse,
    SocialPostCreate, SocialPostRead, SocialPostUpdate,
    SentimentScoreCreate, SentimentScoreRead, SentimentScoreUpdate
)
from app.db.session import get_db
from app.models.social import SocialPost, SentimentScore

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
