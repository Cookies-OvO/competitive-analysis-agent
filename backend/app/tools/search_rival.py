from app.rag.retrieve import search
from app.config import settings


async def search_rival(category: str, price_range: str, dimensions: list[str]) -> dict:
    """从 FAISS 竞品知识库检索各维度口碑，按竞品名 + 维度组织结果"""
    rival_query = f"{category} {price_range} 竞品"
    rival_docs = search(rival_query, settings.rival_index_dir, top_k=10)

    rival_results: dict[str, dict] = {}

    for doc in rival_docs:
        title = doc["title"]
        content = doc["content"]
        score = doc["score"]

        if title not in rival_results:
            rival_results[title] = {}

        for dim in dimensions:
            if dim in content or dim in title:
                if dim not in rival_results[title]:
                    rival_results[title][dim] = []
                rival_results[title][dim].append({
                    "content": content[:500],
                    "score": score,
                })

    return rival_results
