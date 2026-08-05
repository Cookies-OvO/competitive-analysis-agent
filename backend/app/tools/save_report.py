from app.db.engine import AsyncSessionLocal
from app.db.models import Report


async def save_report(state: dict) -> int | None:
    """将分析结果持久化到 reports 表"""
    product_id = state.get("product_id")
    if product_id is None:
        return None

    comparison = state.get("comparison", {})
    full_report = ""
    if isinstance(comparison, dict):
        full_report = comparison.get("detailed_report", "") or str(comparison)

    async with AsyncSessionLocal() as session:
        report = Report(
            product_id=product_id,
            self_summary=state.get("self_summary"),
            rival_summary=state.get("rival_summary"),
            comparison=comparison,
            deep_dive=state.get("deep_dive"),
            full_report=full_report,
        )
        session.add(report)
        await session.commit()
        await session.refresh(report)
        return report.id
