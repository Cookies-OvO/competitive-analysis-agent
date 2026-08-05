# app/rag/ —— RAG 检索增强生成层
# build_index.py: 离线索引流水线 —— 读取 knowledge/*.md → 切分 → 向量化 → 存入 FAISS
# retrieve.py:   在线查询流水线 —— 接收 query → 向量化 → FAISS 检索 → 返回 Top-K
