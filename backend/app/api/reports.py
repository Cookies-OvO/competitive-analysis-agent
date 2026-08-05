from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func
from app.db.engine import AsyncSessionLocal
from app.db.models import Report
from app.schemas import ReportOut

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("", response_model=list[ReportOut])
async def list_reports(
    product_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    async with AsyncSessionLocal() as s:
        stmt = select(Report).order_by(Report.created_at.desc())
        if product_id is not None:
            stmt = stmt.where(Report.product_id == product_id)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await s.execute(stmt)
        return result.scalars().all()


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(report_id: int):
    async with AsyncSessionLocal() as s:
        r = await s.get(Report, report_id)
        if not r:
            raise HTTPException(404, "报告不存在")
        return r


@router.delete("/{report_id}")
async def delete_report(report_id: int):
    async with AsyncSessionLocal() as s:
        r = await s.get(Report, report_id)
        if not r:
            raise HTTPException(404, "报告不存在")
        await s.delete(r)
        await s.commit()
        return {"ok": True}
