import json
import os
from app.state import AgentState
from app.agents_llm import call_llm


async def aggregate_node(state: AgentState) -> dict:
    """多维度对比分析：本品数据 + 竞品数据 → LLM 打分 + 优劣势 + 结论"""
    product_name = state.get("product_name", "未知产品")
    self_data = state.get("self_summary", {})
    rival_data = state.get("rival_summary", {})

    # 格式化本品数据
    self_str = f"产品: {product_name}\n"
    for dim, info in self_data.get("dimensions", {}).items():
        self_str += (
            f"\n### {dim}\n"
            f"- 均分: {info['avg_rating']}/5\n"
            f"- 评价数: {info['review_count']}\n"
            f"- 正面标签: {', '.join(info.get('top_positive', []))}\n"
            f"- 负面标签: {', '.join(info.get('top_negative', []))}\n"
            f"- 代表性评价:\n"
        )
        for comment in info.get("sample_comments", [])[:2]:
            self_str += f"  > {comment}\n"

    # 格式化竞品数据
    rival_str = ""
    for rival_name, dims in rival_data.get("rivals", {}).items():
        rival_str += f"\n## {rival_name}\n"
        for dim, docs in dims.items():
            rival_str += f"\n### {dim}\n"
            for doc in docs:
                rival_str += f"- (相似度{doc['score']:.2f}) {doc['content'][:300]}\n"

    # 读取模板并注入数据
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "aggregate_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    system_prompt = prompt_template.replace("{self_data}", self_str)
    system_prompt = system_prompt.replace("{rival_data}", rival_str)

    raw_response = call_llm(
        system_prompt=system_prompt,
        user_prompt=f"请对 {product_name} 进行竞品对比分析",
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    # 防御性 JSON 解析
    try:
        comparison = json.loads(raw_response)
    except json.JSONDecodeError:
        raw_response = raw_response.strip()
        if raw_response.startswith("```"):
            raw_response = raw_response.split("\n", 1)[1]
            if raw_response.endswith("```"):
                raw_response = raw_response[:-3]
        try:
            comparison = json.loads(raw_response)
        except json.JSONDecodeError:
            comparison = {"raw_response": raw_response, "parse_error": True}

    weaknesses = comparison.get("weaknesses", [])

    return {
        "comparison": comparison,
        "weaknesses": weaknesses,
        "thought_chain": [{
            "agent": "aggregate_node",
            "status": "completed",
            "output": {
                "scores": comparison.get("dimension_scores", {}),
                "strengths": len(comparison.get("strengths", [])),
                "weaknesses": len(weaknesses),
            },
            "detail": comparison.get("conclusion", ""),
        }],
    }
