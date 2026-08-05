from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from app.db.engine import AsyncSessionLocal
from app.db.models import ReviewTag
from app.schemas import ReviewTagCreate, ReviewTagUpdate, ReviewTagOut

router = APIRouter(prefix="/api/review-tags", tags=["review_tags"])


@router.get("", response_model=list[ReviewTagOut])
async def list_tags(review_id: int = Query(...)):
    async with AsyncSessionLocal() as s:
        stmt = select(ReviewTag).where(ReviewTag.review_id == review_id).order_by(ReviewTag.id)
        result = await s.execute(stmt)
        return result.scalars().all()


@router.post("", response_model=ReviewTagOut, status_code=201)
async def create_tag(data: ReviewTagCreate):
    async with AsyncSessionLocal() as s:
        t = ReviewTag(**data.model_dump())
        s.add(t)
        await s.commit()
        await s.refresh(t)
        return t


@router.put("/{tag_id}", response_model=ReviewTagOut)
async def update_tag(tag_id: int, data: ReviewTagUpdate):
    async with AsyncSessionLocal() as s:
        t = await s.get(ReviewTag, tag_id)
        if not t:
            raise HTTPException(404, "标签不存在")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(t, k, v)
        await s.commit()
        await s.refresh(t)
        return t


@router.delete("/{tag_id}")
async def delete_tag(tag_id: int):
    async with AsyncSessionLocal() as s:
        t = await s.get(ReviewTag, tag_id)
        if not t:
            raise HTTPException(404, "标签不存在")
        await s.delete(t)
        await s.commit()
        return {"ok": True}
