from app.state import AgentState
from app.tools.search_rival import search_rival


async def branch_rival_node(state: AgentState) -> dict:
    """从 FAISS 竞品知识库检索同价位竞品在各维度的口碑数据"""
    category = state.get("product_category", "")
    price_range = state.get("price_range", "")
    dimensions = state.get("dimensions", [])

    if not category:
        return {
            "rival_summary": {"error": "产品类目未知，无法检索竞品"},
            "thought_chain": [{
                "agent": "branch_rival_node",
                "status": "error",
                "detail": "product_category 为空",
            }],
        }

    rival_data = await search_rival(
        category=category,
        price_range=price_range,
        dimensions=dimensions,
    )

    rival_count = len(rival_data)
    total_dims = sum(len(dims) for dims in rival_data.values())

    return {
        "rival_summary": {
            "category": category,
            "price_range": price_range,
            "rivals": rival_data,
        },
        "thought_chain": [{
            "agent": "branch_rival_node",
            "status": "completed",
            "output": f"检索到 {rival_count} 个竞品, 覆盖 {total_dims} 个维度",
            "detail": f"价格区间={price_range}, 竞品={list(rival_data.keys())}",
        }],
    }
