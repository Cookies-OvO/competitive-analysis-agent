# app/tools/ —— 工具函数层
# 这些是本项目专用的工具函数，被 nodes/ 中的节点调用。
# 每个工具封装一个具体的数据操作：
#   get_product_info.py: 根据产品名查 products 表
#   query_reviews.py:   按维度聚合 reviews + review_tags
#   search_rival.py:    RAG 检索竞品知识库
