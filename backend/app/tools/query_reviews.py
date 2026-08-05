from sqlalchemy import select
from app.db.engine import AsyncSessionLocal
from app.db.models import Review, ReviewTag


async def query_reviews(product_id: int, dimensions: list[str] | None = None) -> dict:
    """按维度分组聚合评价数据：平均分、评价数、正负面标签、代表性评论"""
    async with AsyncSessionLocal() as session:
        stmt = select(Review).where(Review.product_id == product_id)
        result = await session.execute(stmt)
        reviews = result.scalars().all()

        if not reviews:
            return {}

        grouped: dict[str, dict] = {}

        for review in reviews:
            tags_stmt = select(ReviewTag).where(ReviewTag.review_id == review.id)
            tags_result = await session.execute(tags_stmt)
            tags = tags_result.scalars().all()

            for tag in tags:
                dim = tag.dimension
                if dim is None:
                    continue
                if dimensions and dim not in dimensions:
                    continue

                if dim not in grouped:
                    grouped[dim] = {
                        "ratings": [],
                        "comments": [],
                        "positive_tags": [],
                        "negative_tags": [],
                    }

                grouped[dim]["ratings"].append(review.rating)
                grouped[dim]["comments"].append(review.content)
                if tag.sentiment == "positive":
                    grouped[dim]["positive_tags"].append(tag.tag_name)
                elif tag.sentiment == "negative":
                    grouped[dim]["negative_tags"].append(tag.tag_name)

        result_dict = {}
        for dim, data in grouped.items():
            ratings = data["ratings"]
            avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 0

            pos_counts = {}
            for t in data["positive_tags"]:
                pos_counts[t] = pos_counts.get(t, 0) + 1
            top_positive = sorted(pos_counts, key=pos_counts.get, reverse=True)[:3]

            neg_counts = {}
            for t in data["negative_tags"]:
                neg_counts[t] = neg_counts.get(t, 0) + 1
            top_negative = sorted(neg_counts, key=neg_counts.get, reverse=True)[:3]

            sample_comments = data["comments"][:3]

            result_dict[dim] = {
                "avg_rating": avg_rating,
                "review_count": len(ratings),
                "top_positive": top_positive,
                "top_negative": top_negative,
                "sample_comments": sample_comments,
            }

        return result_dict
