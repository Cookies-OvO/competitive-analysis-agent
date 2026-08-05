from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from app.db.engine import AsyncSessionLocal
from app.db.models import Product, Review
from app.schemas import ReviewCreate, ReviewUpdate, ReviewOut

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("", response_model=list[ReviewOut])
async def list_reviews(product_id: int | None = Query(None)):
    async with AsyncSessionLocal() as s:
        stmt = select(Review).order_by(Review.id)
        if product_id is not None:
            stmt = stmt.where(Review.product_id == product_id)
        result = await s.execute(stmt)
        return result.scalars().all()


@router.get("/{review_id}", response_model=ReviewOut)
async def get_review(review_id: int):
    async with AsyncSessionLocal() as s:
        r = await s.get(Review, review_id)
        if not r:
            raise HTTPException(404, "评价不存在")
        return r


@router.post("", response_model=ReviewOut, status_code=201)
async def create_review(data: ReviewCreate):
    async with AsyncSessionLocal() as s:
        p = await s.get(Product, data.product_id)
        if not p:
            raise HTTPException(404, "产品不存在")
        r = Review(**data.model_dump())
        s.add(r)
        await s.commit()
        await s.refresh(r)
        return r


@router.put("/{review_id}", response_model=ReviewOut)
async def update_review(review_id: int, data: ReviewUpdate):
    async with AsyncSessionLocal() as s:
        r = await s.get(Review, review_id)
        if not r:
            raise HTTPException(404, "评价不存在")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(r, k, v)
        await s.commit()
        await s.refresh(r)
        return r


@router.delete("/{review_id}")
async def delete_review(review_id: int):
    async with AsyncSessionLocal() as s:
        r = await s.get(Review, review_id)
        if not r:
            raise HTTPException(404, "评价不存在")
        await s.delete(r)
        await s.commit()
        return {"ok": True}
