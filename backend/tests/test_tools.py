"""
tests/test_tools.py —— 工具函数单元测试
========================================
测试三个核心工具函数的正确性：
  1. get_product_info — 产品搜索
  2. query_reviews    — 评价聚合
  3. search_rival     — 竞品检索（需要先构建FAISS索引）

运行方式：
  pytest tests/test_tools.py -v
"""
import asyncio
import pytest


class TestGetProductInfo:
    """测试产品搜索工具"""

    def test_search_existing_product(self):
        """测试搜索存在的产品"""
        from app.tools.get_product_info import get_product_info
        results = asyncio.run(get_product_info("运动手环9pro"))
        assert len(results) > 0, "应该找到至少一个匹配产品"
        assert results[0]["name"] == "运动手环9pro"
        assert results[0]["price"] == 245.0

    def test_search_nonexistent_product(self):
        """测试搜索不存在的产品"""
        from app.tools.get_product_info import get_product_info
        results = asyncio.run(get_product_info("不存在的产品XYZ"))
        assert len(results) == 0, "不应该找到任何产品"

    def test_search_fuzzy(self):
        """测试模糊搜索"""
        from app.tools.get_product_info import get_product_info
        results = asyncio.run(get_product_info("手环"))
        assert len(results) > 0, "应该找到包含手环关键词的产品"


class TestQueryReviews:
    """测试评价聚合工具"""

    def test_query_reviews_for_product_1(self):
        """测试查询运动手环9pro的评价聚合"""
        from app.tools.query_reviews import query_reviews
        data = asyncio.run(query_reviews(product_id=2, dimensions=["续航", "屏幕", "性价比"]))
        assert "续航" in data
        assert "屏幕" in data
        assert "性价比" in data
        # 续航应该有至少1条评价
        assert data["续航"]["review_count"] >= 1
        # 评分应该在1-5之间
        assert 1 <= data["续航"]["avg_rating"] <= 5

    def test_query_reviews_with_no_dimensions(self):
        """测试不限制维度的情况"""
        from app.tools.query_reviews import query_reviews
        data = asyncio.run(query_reviews(product_id=2))
        assert len(data) > 0, "应该返回至少一个维度"


class TestSearchRival:
    """测试竞品检索工具（需要在构建FAISS索引后运行）"""

    def test_search_rival_basic(self):
        """测试基本的竞品检索"""
        from app.tools.search_rival import search_rival
        try:
            results = asyncio.run(search_rival(
                category="智能手环",
                price_range="200-300元",
                dimensions=["续航", "屏幕"],
            ))
            assert isinstance(results, dict), "应该返回dict"
        except FileNotFoundError:
            pytest.skip("FAISS 索引未构建，跳过检索测试")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
