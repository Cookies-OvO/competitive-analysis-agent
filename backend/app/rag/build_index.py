import os
import json
import asyncio
import re
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from sentence_transformers import SentenceTransformer
import faiss
from sqlalchemy import select
from app.config import settings
from app.db.engine import AsyncSessionLocal
from app.db.models import Product
from app.agents_llm import call_llm

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


RIVAL_PROMPT = """你是一个{category}品类的资深市场分析师。以下是店铺数据库中的一款产品：

- 产品名称：{name}
- 品牌：{brand}
- 售价：{price}元
- 类目：{category}

请基于你对 {category} 市场的真实了解，生成一份详尽的竞品分析报告。要求：

1. 列出 5-8 个同价位段（{price_low}-{price_high}元）的真实竞品，覆盖主流品牌
2. 每个竞品至少从 5 个维度详细分析，包括但不限于：核心配置、功能特色、用户口碑、优缺点、性价比
3. 每个竞品需标注：售价、品牌、各维度评分(1-10分)、核心用户画像、与「{name}」的优劣势对比
4. 还需要包含：
   - 该价位段的市场格局分析
   - 消费者选购建议（不同需求选什么）
   - 同品类高价位和低价位段的核心差异点

请输出详细的 Markdown 格式，每个主题（每个竞品、总结合）各用一个 ## 二级标题开头。内容尽量充实，不要过于简短。"""


IMPROVE_PROMPT = """你是一个{category}品类的产品改进与用户体验专家。店铺里有一款产品：

- 产品名称：{name}
- 售价：{price}元
- 类目：{category}

请基于你对 {category} 品类的深入了解，生成一份产品改进分析报告。要求：

1. 列出该价位段 {category} 产品最常见的 5-8 个用户痛点/差评方向
2. 每个痛点的详细改进方案，包含：
   - 具体改进措施（技术方案/设计调整/软件优化等）
   - 行业参考案例（其他品牌怎么解决的）
   - 预估改进成本（低/中/高）
   - 改进后预期效果
3. 还需要包含：
   - 该品类下一代产品的趋势预判
   - 可以做差异化的创新方向
   - 从用户评价中提炼的未满足需求

请输出详细的 Markdown 格式，每个改进方向各用一个 ## 二级标题开头。内容尽量具体可落地，避免泛泛而谈。"""


def load_embedding_model() -> SentenceTransformer:
    # 国内网络优先用 HF 镜像，避免连接超时
    if not os.environ.get("HF_ENDPOINT"):
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    print(f"  加载 Embedding: {settings.embedding_model} ...")
    return SentenceTransformer(settings.embedding_model)


async def _load_products() -> list[dict]:
    async with AsyncSessionLocal() as s:
        result = await s.execute(select(Product).order_by(Product.id))
        rows = result.scalars().all()
        return [
            {"name": r.name, "brand": r.brand, "price": r.price or 0, "category": r.category}
            for r in rows
        ]


def _price_range(price: float) -> tuple[int, int]:
    if price <= 0:
        return 0, 500
    low = max(0, int(price * 0.5))
    high = int(price * 1.5) + 50
    return low, high


def _sanitize_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    return re.sub(r'[\ud800-\udfff]', '', text)


def _parse_llm_response(text: str, fallback_title: str = "") -> list[dict]:
    """按 ## 标题切分 LLM 输出"""
    chunks = []
    current_title = ""
    current_lines = []

    for line in text.split("\n"):
        if line.startswith("## "):
            if current_title and current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    chunks.append({"title": current_title, "content": content})
            current_title = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_title and current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            chunks.append({"title": current_title, "content": content})

    if not chunks and text.strip():
        title = fallback_title or "知识片段"
        chunks.append({"title": title, "content": text.strip()})

    return chunks


def _call_llm_safe(system: str, prompt: str, label: str) -> str:
    try:
        return _sanitize_text(call_llm(system_prompt=system, user_prompt=prompt, temperature=0.3))
    except Exception as e:
        print(f"  [WARN] LLM 调用失败({label}): {e}")
        return ""


def generate_rival_chunks(products: list[dict], on_progress=None) -> list[dict]:
    chunks = []
    for p in products:
        price = p["price"] or 0
        pl, ph = _price_range(price)
        brand = p["brand"] or "未知品牌"
        cat = p["category"]
        name = p["name"]

        if on_progress:
            on_progress(f"生成竞品分析: {name}")

        prompt = RIVAL_PROMPT.format(
            name=name, brand=brand,
            price=f"{price:.0f}" if price else "未知",
            category=cat, price_low=pl, price_high=ph,
        )

        print(f"  LLM 生成竞品分析: {name} ({cat})")
        response = _call_llm_safe(
            f"你是{cat}市场研究专家。请输出详细、充实的 Markdown 分析报告，内容不少于 1500 字。",
            prompt, name,
        )
        if response:
            chunks.extend(_parse_llm_response(response, fallback_title=name))

    if len(products) > 1 and len(set(p["category"] for p in products)) > 1:
        if on_progress:
            on_progress("生成跨品类竞争格局")
        cats = ", ".join(sorted(set(p["category"] for p in products)))
        names = ", ".join(p["name"] for p in products)
        summary_prompt = f"""店铺目前在售产品：{names}，覆盖品类：{cats}。
请基于这些品类，分析当前消费电子市场的整体竞争格局、各品类的差异化竞争策略、以及店铺的产品线协同建议。
用 Markdown 格式输出，每个主题用 ## 标题。"""
        response = _call_llm_safe(
            "你是消费电子市场战略分析师，请输出详实的分析。", summary_prompt, "跨品类总结合"
        )
        if response:
            chunks.extend(_parse_llm_response(response, fallback_title="跨品类格局"))

    return chunks


def generate_improve_chunks(products: list[dict], on_progress=None) -> list[dict]:
    chunks = []
    seen = set()
    for p in products:
        cat = p["category"]
        if cat in seen:
            continue
        seen.add(cat)

        price = p["price"] or 0

        if on_progress:
            on_progress(f"生成改进案例: {p['name']}")

        prompt = IMPROVE_PROMPT.format(
            name=p["name"],
            price=f"{price:.0f}" if price else "未知",
            category=cat,
        )

        print(f"  LLM 生成改进案例: {p['name']} ({cat})")
        response = _call_llm_safe(
            f"你是{cat}改进顾问。请输出详细、可落地的改进分析报告，内容不少于 1500 字。",
            prompt, p["name"],
        )
        if response:
            chunks.extend(_parse_llm_response(response, fallback_title=p["name"]))

    return chunks


def build_faiss_index(chunks: list[dict], index_dir: str, model: SentenceTransformer):
    if not chunks:
        print(f"  [SKIP] 无文本块，跳过 {index_dir}")
        return

    texts = [f"# {c['title']}\n{c['content']}" for c in chunks]
    print(f"  文本块数: {len(texts)}")

    embeddings = model.encode(texts, normalize_embeddings=True)
    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)
    index.add(embeddings.astype(np.float32))

    os.makedirs(index_dir, exist_ok=True)
    faiss.write_index(index, os.path.join(index_dir, "index.faiss"))
    with open(os.path.join(index_dir, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"  [OK] 索引已保存: {index_dir}/")


def build_stream(on_event):
    """SSE 流式构建知识库。竞品+改进案例的生成和索引并行执行。"""
    on_event("start", "开始构建知识库...")

    on_event("loading", "读取数据库产品...")
    products = asyncio.run(_load_products())
    if not products:
        on_event("error", "数据库中没有产品，请先添加产品")
        return
    on_event("loading", f"读取到 {len(products)} 款产品")

    on_event("loading", "加载 Embedding 模型...")
    model = load_embedding_model()

    on_event("rival", "LLM 生成竞品分析...")
    on_event("improve", "LLM 生成改进案例...")

    rival_result = []
    improve_result = []

    def build_rival():
        chunks = generate_rival_chunks(products,
            on_progress=lambda msg: on_event("rival", msg))
        on_event("rival", f"竞品分析生成完成，共 {len(chunks)} 个文本块")
        on_event("rival_index", "构建竞品向量索引...")
        build_faiss_index(chunks, settings.rival_index_dir, model)
        on_event("rival_index", f"竞品索引完成 ({len(chunks)} 块)")
        return chunks

    def build_improve():
        chunks = generate_improve_chunks(products,
            on_progress=lambda msg: on_event("improve", msg))
        on_event("improve", f"改进案例生成完成，共 {len(chunks)} 个文本块")
        on_event("improve_index", "构建改进案例索引...")
        build_faiss_index(chunks, settings.improve_index_dir, model)
        on_event("improve_index", f"改进案例索引完成 ({len(chunks)} 块)")
        return chunks

    with ThreadPoolExecutor(max_workers=2) as executor:
        f_rival = executor.submit(build_rival)
        f_improve = executor.submit(build_improve)
        for f in as_completed([f_rival, f_improve]):
            try:
                if f is f_rival:
                    rival_result = f.result()
                else:
                    improve_result = f.result()
            except Exception as e:
                on_event("error", f"构建失败: {e}")
                raise

    from app.rag import retrieve
    retrieve._index_cache.clear()

    on_event("done", f"知识库重建完成！竞品 {len(rival_result)} 块，改进 {len(improve_result)} 块")


def build_all():
    """CLI 同步构建入口"""
    print("=" * 60)
    print("  FAISS 知识库索引构建（LLM 动态生成）")
    print("=" * 60)

    steps = []

    def collect(step, msg):
        print(f"  [{step}] {msg}")
        steps.append((step, msg))

    build_stream(collect)

    print(f"\n[OK] 构建完成")


if __name__ == "__main__":
    build_all()
