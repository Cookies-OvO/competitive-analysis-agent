import os
from sqlalchemy import select, and_
from app.state import AgentState
from app.agents_llm import call_llm
from app.rag.retrieve import search
from app.db.engine import AsyncSessionLocal
from app.db.models import Review, ReviewTag
from app.config import settings


async def deep_dive_node(state: AgentState) -> dict:
    """对每个短板维度：查DB差评 + RAG改进案例 + LLM生成分析报告"""
    product_name = state.get("product_name", "未知产品")
    product_id = state.get("product_id")
    weaknesses = state.get("weaknesses", [])

    if not weaknesses:
        return {
            "deep_dive": "所有维度表现良好，无需深挖改进。",
            "thought_chain": [{
                "agent": "deep_dive_node",
                "status": "skipped",
                "detail": "无短板需要深挖",
            }],
        }

    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "deep_dive_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    all_reports = []

    for weakness in weaknesses:
        dim = weakness.get("维度", "")
        percentage = weakness.get("差距", 0)
        description = weakness.get("描述", "")

        # A. 查数据库差评
        bad_reviews_text = ""
        if product_id:
            async with AsyncSessionLocal() as session:
                stmt = (
                    select(Review)
                    .join(ReviewTag, Review.id == ReviewTag.review_id)
                    .where(
                        and_(
                            Review.product_id == product_id,
                            ReviewTag.dimension == dim,
                            Review.rating <= 2,
                        )
                    )
                    .limit(5)
                )
                result = await session.execute(stmt)
                bad_reviews = result.scalars().all()
                bad_reviews_text = "\n".join([
                    f"- [{r.rating}星] {r.content}" for r in bad_reviews
                ])

        if not bad_reviews_text:
            bad_reviews_text = f"暂无该维度的详细差评数据\n描述: {description}"

        # B. FAISS 检索改进案例
        try:
            cases = search(f"{dim} 改进方案", settings.improve_index_dir, top_k=3)
            improve_cases_text = "\n".join([
                f"### {c['title']}\n{c['content'][:400]}" for c in cases
            ])
        except FileNotFoundError:
            improve_cases_text = "（改进案例索引未构建，请先运行 python -m app.rag.build_index）"

        # C. 填充模板 → LLM 生成报告
        filled_prompt = prompt_template.replace("{product_name}", product_name)
        filled_prompt = filled_prompt.replace("{dimension}", dim)
        filled_prompt = filled_prompt.replace("{percentage}", str(percentage))
        filled_prompt = filled_prompt.replace("{bad_reviews}", bad_reviews_text)
        filled_prompt = filled_prompt.replace("{improve_cases}", improve_cases_text)

        report = call_llm(
            system_prompt=filled_prompt,
            user_prompt=f"请对 {product_name} 的 {dim} 维度进行深挖分析",
            temperature=0.1,
        )

        all_reports.append(f"## {dim} 深挖分析\n\n{report}")

    full_deep_dive = "\n\n---\n\n".join(all_reports)

    return {
        "deep_dive": full_deep_dive,
        "thought_chain": [{
            "agent": "deep_dive_node",
            "status": "completed",
            "output": full_deep_dive[:200] + "...",
            "detail": f"对 {len(weaknesses)} 个短板维度完成深挖分析",
        }],
    }
