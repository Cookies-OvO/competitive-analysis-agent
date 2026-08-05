# app/nodes/ —— LangGraph 节点层
# 每个节点是图中的一个处理步骤（Node），对应文档中 LangGraph 图结构的 5 个节点：
#
#   ① plan_node.py          —— 制定分析计划（LLM 解析意图 + DB 确认产品）
#   ② branch_self_node.py   —— 查询本品各维度评价聚合（DB reviews + tags）
#   ③ branch_rival_node.py  —— 检索竞品各维度口碑（RAG FAISS 竞品知识库）
#   ④ aggregate_node.py     —— 本品 vs 竞品多维度对比分析（LLM 生成报告）
#   ⑤ deep_dive_node.py     —— 短板深挖分析（DB 差评 + RAG 改进案例 → LLM 建议）
#
# 节点执行顺序（对应文档中 LangGraph 图结构）：
#   START → plan → [branch_self 并行 branch_rival] → aggregate
#         → should_deep_dive? → (是) deep_dive → END
#                             → (否) END
