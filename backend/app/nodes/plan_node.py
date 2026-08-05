import json
import os
from app.state import AgentState
from app.tools.get_product_info import get_product_info
from app.agents_llm import call_llm


async def plan_node(state: AgentState) -> dict:
    """工作流入口：LLM 解析用户意图 → 匹配产品 + 确定维度 + 推算价格区间"""
    user_msg = state.get("user_message", "")

    products = await get_product_info(user_msg)

    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "plan_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    system_prompt = prompt_template.replace("{question}", user_msg)
    products_str = "\n".join([
        f"- ID:{p['id']}, {p['name']}, {p['brand']}, ¥{p['price']}, {p['category']}"
        for p in products
    ])
    system_prompt = system_prompt.replace("{products}", products_str)

    raw_response = call_llm(
        system_prompt=system_prompt,
        user_prompt="请根据用户问题，从候选产品中选出目标产品并制定竞品分析计划",
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    try:
        plan = json.loads(raw_response)
    except json.JSONDecodeError:
        plan = {}

    llm_product_id = plan.get("product_id", 0)

    if llm_product_id == 0:
        return {
            "product_name": user_msg,
            "thought_chain": [{
                "agent": "plan",
                "status": "error",
                "detail": f"未在数据库中匹配到产品: {user_msg[:30]}",
            }],
        }

    product = next((p for p in products if p["id"] == llm_product_id), None)
    if product is None:
        return {
            "product_name": user_msg,
            "thought_chain": [{
                "agent": "plan",
                "status": "error",
                "detail": f"LLM 返回了无效的产品ID: {llm_product_id}",
            }],
        }

    product_id = product["id"]
    product_name = product["name"]
    product_category = product["category"]
    product_price = product["price"]

    dimensions = plan.get("dimensions", [])
    price_range = f"{max(50, product_price - 50):.0f}-{product_price + 50:.0f}元"

    return {
        "product_id": product_id,
        "product_name": product_name,
        "product_category": product_category,
        "price_range": price_range,
        "dimensions": dimensions,
        "thought_chain": [{
            "agent": "plan_node",
            "status": "completed",
            "input": user_msg,
            "output": {
                "产品": product_name,
                "类目": product_category,
                "价格": product_price,
                "维度": dimensions,
                "价格区间": price_range,
            },
            "detail": f"确定本品={product_name}, 分析维度={len(dimensions)}个",
        }],
    }
