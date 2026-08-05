from sqlalchemy import select
from app.db.engine import AsyncSessionLocal
from app.db.models import Product


async def get_product_info(user_input: str) -> list[dict]:
    """加载全部产品，不做过滤——选品由 LLM 决定，不靠写死的字符串匹配"""
    async with AsyncSessionLocal() as session:
        stmt = select(Product)
        result = await session.execute(stmt)
        all_products = result.scalars().all()

        return [
            {
                "id": p.id,
                "name": p.name,
                "brand": p.brand,
                "price": p.price,
                "category": p.category,
            }
            for p in all_products
        ]
