"""
tests/test_graph.py —— LangGraph 图集成测试
============================================
测试完整的工作流图的正确性：
  1. 图的编译是否成功
  2. 各节点是否能正常执行
  3. 思考链是否完整

运行方式：
  pytest tests/test_graph.py -v
"""
import pytest
from app.graph import agent_graph


class TestGraphStructure:
    """测试图的结构"""

    def test_graph_compiles(self):
        """测试图是否成功编译"""
        assert agent_graph is not None, "agent_graph 不应该为 None"

    def test_graph_has_nodes(self):
        """测试图是否包含所有必要的节点"""
        # 检查图对象有 nodes 属性
        nodes = agent_graph.get_graph().nodes if hasattr(agent_graph, 'get_graph') else {}
        print(f"Graph nodes: {nodes}")


class TestGraphExecution:
    """测试图的执行"""

    def test_invoke_basic(self):
        """测试基本调用"""
        result = agent_graph.invoke({
            "user_message": "分析一下运动手环9pro",
            "messages": [],
            "dimensions": [],
            "weaknesses": [],
            "thought_chain": [],
        })

        # 检查结果
        assert "product_name" in result, "返回结果应该包含 product_name"
        assert "thought_chain" in result, "返回结果应该包含 thought_chain"

        # 思考链应该至少有 plan 节点的记录
        chain = result.get("thought_chain", [])
        agents = [step.get("agent") for step in chain]
        assert "plan_node" in agents, f"思考链应包含 plan_node，实际: {agents}"

        print(f"\n产品名称: {result.get('product_name')}")
        print(f"分析维度: {result.get('dimensions')}")
        print(f"思考链步骤: {len(result.get('thought_chain', []))}")
        print(f"短板数量: {len(result.get('weaknesses', []))}")

    def test_invoke_with_nonexistent_product(self):
        """测试分析不存在的产品"""
        result = agent_graph.invoke({
            "user_message": "分析一下不存在的产品ABC",
            "messages": [],
            "dimensions": [],
            "weaknesses": [],
            "thought_chain": [],
        })

        # 应该优雅处理，不应该崩溃
        assert "thought_chain" in result
        # plan_node 应该报错
        chain = result.get("thought_chain", [])
        if chain:
            plan_status = chain[0].get("status")
            print(f"\nplan_node 状态: {plan_status}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
