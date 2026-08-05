from langgraph.graph import StateGraph, END
from app.state import AgentState
from app.nodes.plan_node import plan_node
from app.nodes.branch_self_node import branch_self_node
from app.nodes.branch_rival_node import branch_rival_node
from app.nodes.aggregate_node import aggregate_node
from app.nodes.deep_dive_node import deep_dive_node
from app.config import settings


def should_deep_dive(state: AgentState) -> str:
    """聚合后的条件路由：任一维度本品评分 < 阈值 → 深挖，否则结束"""
    weaknesses = state.get("weaknesses", [])
    if not weaknesses:
        return END
    threshold = settings.deep_dive_threshold
    for w in weaknesses:
        if w.get("本品评分", 100) < threshold:
            return "deep_dive"
    return END


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("plan", plan_node)
    workflow.add_node("self", branch_self_node)
    workflow.add_node("rival", branch_rival_node)
    workflow.add_node("aggregate", aggregate_node)
    workflow.add_node("deep_dive", deep_dive_node)

    workflow.set_entry_point("plan")

    # plan → self ∥ rival（并行）
    workflow.add_edge("plan", "self")
    workflow.add_edge("plan", "rival")

    # self + rival → aggregate（汇聚）
    workflow.add_edge("self", "aggregate")
    workflow.add_edge("rival", "aggregate")

    # aggregate → deep_dive / END（条件路由）
    workflow.add_conditional_edges(
        "aggregate",
        should_deep_dive,
        {"deep_dive": "deep_dive", END: END},
    )

    workflow.add_edge("deep_dive", END)

    return workflow.compile()


agent_graph = build_graph()
