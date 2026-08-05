import json
import os
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.rag.build_index import build_stream
from app.config import settings

router = APIRouter(prefix="/api/rag", tags=["rag"])


def _get_index_stats(index_dir: str) -> dict | None:
    chunks_file = os.path.join(index_dir, "chunks.json")
    index_file = os.path.join(index_dir, "index.faiss")
    if not os.path.exists(chunks_file) or not os.path.exists(index_file):
        return None
    try:
        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        stat = os.stat(index_file)
        return {
            "chunk_count": len(chunks),
            "file_size_kb": round(stat.st_size / 1024, 1),
            "last_modified": stat.st_mtime,
        }
    except Exception:
        return None


@router.get("/status")
async def rag_status():
    rival = _get_index_stats(settings.rival_index_dir)
    improve = _get_index_stats(settings.improve_index_dir)

    ready = rival is not None and improve is not None
    total_chunks = (rival["chunk_count"] if rival else 0) + (improve["chunk_count"] if improve else 0)
    last_modified = 0
    if rival:
        last_modified = max(last_modified, rival["last_modified"])
    if improve:
        last_modified = max(last_modified, improve["last_modified"])

    return {
        "ready": ready,
        "total_chunks": total_chunks,
        "rival": rival,
        "improve": improve,
        "last_modified": last_modified if last_modified else None,
    }


@router.post("/rebuild")
async def rebuild_index():
    """SSE 流式重建知识库：从数据库读产品 → LLM 生成分析 → 并行构建向量索引"""
    queue = asyncio.Queue()

    def on_event(step: str, message: str):
        queue.put_nowait((step, message))

    async def event_generator():
        task = asyncio.create_task(asyncio.to_thread(build_stream, on_event))

        while True:
            try:
                step, message = await asyncio.wait_for(queue.get(), timeout=600)
                yield f"data: {json.dumps({'step': step, 'message': message}, ensure_ascii=False)}\n\n"
                if step == "done" or step == "error":
                    break
            except asyncio.TimeoutError:
                break

        await task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
