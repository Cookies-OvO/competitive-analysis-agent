import operator
from typing import TypedDict, Optional, Annotated, Sequence
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """LangGraph 共享状态。并行节点写 thought_chain 时靠 operator.add 自动合并。"""

    # 框架字段
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # 用户输入
    user_message: str

    # plan_node 产出
    product_id: Optional[int]
    product_name: Optional[str]
    product_category: Optional[str]
    price_range: Optional[str]
    dimensions: list[str]

    # branch_self_node 产出
    self_summary: Optional[dict]

    # branch_rival_node 产出
    rival_summary: Optional[dict]

    # aggregate_node 产出
    comparison: Optional[dict]
    weaknesses: list[dict]

    # deep_dive_node 产出
    deep_dive: Optional[str]

    # 最终输出（预留）
    final_report: Optional[str]

    # 思考链 — reducer = operator.add 保证并行节点追加不覆盖
    thought_chain: Annotated[list[dict], operator.add]
