from app.state import AgentState
from app.tools.query_reviews import query_reviews


async def branch_self_node(state: AgentState) -> dict:
    """查询本品各维度评价聚合数据（评分、标签、原文）"""
    product_id = state.get("product_id")
    product_name = state.get("product_name", "未知产品")
    dimensions = state.get("dimensions", [])

    if product_id is None:
        return {
            "self_summary": {"error": "未找到本品，请检查产品名称是否正确"},
            "thought_chain": [{
                "agent": "branch_self_node",
                "status": "error",
                "detail": "product_id 为空，无法查询评价数据",
            }],
        }

    data = await query_reviews(product_id, dimensions)

    self_summary = {
        "product_id": product_id,
        "product_name": product_name,
        "dimensions": data,
    }

    dim_scores = {}
    for dim in dimensions:
        if dim in data:
            dim_scores[dim] = data[dim]["avg_rating"]

    return {
        "self_summary": self_summary,
        "thought_chain": [{
            "agent": "branch_self_node",
            "status": "completed",
            "output": dim_scores,
            "detail": f"本品 {product_name} 各维度评分: {dim_scores}",
        }],
    }
