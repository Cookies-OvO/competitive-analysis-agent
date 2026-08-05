from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.db.engine import AsyncSessionLocal
from app.db.models import Product
from app.schemas import ProductCreate, ProductUpdate, ProductOut

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
async def list_products():
    async with AsyncSessionLocal() as s:
        result = await s.execute(select(Product).order_by(Product.id))
        return result.scalars().all()


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int):
    async with AsyncSessionLocal() as s:
        p = await s.get(Product, product_id)
        if not p:
            raise HTTPException(404, "产品不存在")
        return p


@router.post("", response_model=ProductOut, status_code=201)
async def create_product(data: ProductCreate):
    async with AsyncSessionLocal() as s:
        p = Product(**data.model_dump())
        s.add(p)
        await s.commit()
        await s.refresh(p)
        return p


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(product_id: int, data: ProductUpdate):
    async with AsyncSessionLocal() as s:
        p = await s.get(Product, product_id)
        if not p:
            raise HTTPException(404, "产品不存在")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(p, k, v)
        await s.commit()
        await s.refresh(p)
        return p


@router.delete("/{product_id}")
async def delete_product(product_id: int):
    async with AsyncSessionLocal() as s:
        p = await s.get(Product, product_id)
        if not p:
            raise HTTPException(404, "产品不存在")
        await s.delete(p)
        await s.commit()
        return {"ok": True}
