import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.graph import agent_graph
from app.config import settings
from app.tools.save_report import save_report
from app.api.products import router as products_router
from app.api.reviews import router as reviews_router
from app.api.review_tags import router as review_tags_router
from app.api.reports import router as reports_router
from app.api.rag import router as rag_router

app = FastAPI(
    title="竞品分析 Agent 系统",
    description="基于 LangGraph 的多 Agent 竞品分析系统",
    version="1.0.0",
)

app.include_router(products_router)
app.include_router(reviews_router)
app.include_router(review_tags_router)
app.include_router(reports_router)
app.include_router(rag_router)


class AnalyzeRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class AnalyzeResponse(BaseModel):
    product_name: str
    comparison_report: str
    weaknesses: list[dict] = Field(default_factory=list)
    deep_dive: str | None = None
    thought_chain: list[dict] = Field(default_factory=list)


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """同步竞品分析：plan → self∥rival → aggregate → deep_dive(按需)"""
    initial_state = {
        "user_message": req.message,
        "messages": [],
        "dimensions": [],
        "weaknesses": [],
        "thought_chain": [],
    }

    result = await agent_graph.ainvoke(initial_state)
    await save_report(result)

    comparison = result.get("comparison", {})
    detailed_report = comparison.get("detailed_report", "") if isinstance(comparison, dict) else ""

    if not detailed_report and isinstance(comparison, dict):
        detailed_report = json.dumps(comparison, ensure_ascii=False, indent=2)

    return AnalyzeResponse(
        product_name=result.get("product_name", ""),
        comparison_report=detailed_report,
        weaknesses=result.get("weaknesses", []),
        deep_dive=result.get("deep_dive"),
        thought_chain=result.get("thought_chain", []),
    )


@app.post("/api/analyze/stream")
async def analyze_stream(req: AnalyzeRequest):
    """SSE 流式分析：实时推送 thought 事件 + 最终 result 事件"""

    async def event_generator():
        initial_state = {
            "user_message": req.message,
            "messages": [],
            "dimensions": [],
            "weaknesses": [],
            "thought_chain": [],
        }

        sent_thoughts = 0

        try:
            final_state = None
            async for state in agent_graph.astream(initial_state, stream_mode="values"):
                final_state = state
                chain = state.get("thought_chain", [])
                while sent_thoughts < len(chain):
                    yield f"data: {json.dumps({'event': 'thought', 'data': chain[sent_thoughts]}, ensure_ascii=False)}\n\n"
                    sent_thoughts += 1

            if final_state:
                await save_report(final_state)

        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'data': str(e)}, ensure_ascii=False)}\n\n"
            return

        if final_state:
            comparison = final_state.get("comparison", {})
            report = comparison.get("detailed_report", "") if isinstance(comparison, dict) else str(comparison)

            result_data = {
                "event": "result",
                "data": {
                    "product_name": final_state.get("product_name", ""),
                    "comparison_report": report,
                    "weaknesses": final_state.get("weaknesses", []),
                    "deep_dive": final_state.get("deep_dive"),
                },
            }
            yield f"data: {json.dumps(result_data, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'event': 'done', 'data': {}}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
