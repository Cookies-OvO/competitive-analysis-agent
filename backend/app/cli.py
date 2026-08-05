import asyncio
from app.graph import agent_graph
from app.tools.save_report import save_report


def print_separator(char: str = "=", length: int = 60):
    print(char * length)


def print_header():
    print("""
+----------------------------------------------------------+
|        竞品分析 Agent 系统  v1.0                          |
|    LangGraph 多 Agent 竞品分析                             |
|                                                          |
|    输入产品名，自动对比本品与竞品各维度表现                |
|    输入 /quit 退出    输入 /help 查看帮助                  |
+----------------------------------------------------------+
    """)


def print_thought_chain(chain: list[dict]):
    if not chain:
        return

    print("\n" + "=" * 60)
    print("  [思考链] Agent 处理过程")
    print("=" * 60)

    for step in chain:
        agent = step.get("agent", "unknown")
        status = step.get("status", "?")
        detail = step.get("detail", "")
        output = step.get("output", "")

        icon = {
            "completed": "[OK]",
            "error": "[ERROR]",
            "skipped": "[SKIP]",
            "warning": "[WARN]",
        }.get(status, "[?]")

        print(f"  {icon} [{agent}]")
        if detail:
            print(f"     {detail}")
        if output and isinstance(output, dict):
            for k, v in output.items():
                print(f"     |-- {k}: {v}")

    print("=" * 60)


def print_self_summary(self_data: dict):
    dimensions = self_data.get("dimensions", {})
    if not dimensions:
        return

    print("\n  +-- 本品评价聚合" + "-" * 44)
    for dim, info in dimensions.items():
        avg = info.get("avg_rating", 0)
        count = info.get("review_count", 0)
        pos = info.get("top_positive", [])
        neg = info.get("top_negative", [])

        bar_len = int(avg * 4)
        bar = "#" * bar_len + "-" * (20 - bar_len)

        print(f"  | {dim}: {bar} {avg}/5 ({count}条评价)")
        if pos:
            print(f"  |   正面: {', '.join(pos)}")
        if neg:
            print(f"  |   负面: {', '.join(neg)}")
    print("  +" + "-" * 50)


def print_report(report: str):
    if not report:
        return
    print("\n  +-- 竞品对比报告" + "-" * 44)
    lines = report.split("\n")
    for line in lines[:40]:
        print(f"  | {line}")
    if len(lines) > 40:
        print(f"  | ... (共 {len(lines)} 行，完整报告见 API 输出)")
    print("  +" + "-" * 50)


def print_deep_dive(deep_dive: str):
    if not deep_dive or deep_dive.startswith("所有维度"):
        return
    print("\n  +-- 短板深挖分析" + "-" * 44)
    lines = deep_dive.split("\n")
    for line in lines[:30]:
        print(f"  | {line}")
    if len(lines) > 30:
        print(f"  | ... (共 {len(lines)} 行)")
    print("  +" + "-" * 50)


async def main():
    print_header()

    while True:
        try:
            user_input = input("\n  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  再见！")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit", "quit", "exit"):
            print("  再见！")
            break

        if user_input.lower() in ("/help", "help"):
            print("""
  +-- 使用说明 ---------------------------------
  | 输入产品名称即可开始竞品分析，例如:
  |   分析一下运动手环9pro
  |   运动手环9pro的竞品表现如何
  |   对比一下华为手环8
  |
  | 支持的命令:
  |   /quit, /exit  — 退出
  |   /help         — 显示本帮助
  +----------------------------------------------
            """)
            continue

        print("\n  [分析中... 可能需要 10-30 秒]\n")

        result = await agent_graph.ainvoke({
            "user_message": user_input,
            "messages": [],
            "dimensions": [],
            "weaknesses": [],
            "thought_chain": [],
        })

        report_id = await save_report(result)

        print(f"  [产品] {result.get('product_name', 'N/A')}")
        print(f"  [维度] {', '.join(result.get('dimensions', []))}")

        self_data = result.get("self_summary", {})
        print_self_summary(self_data)

        rival_data = result.get("rival_summary", {})
        rivals = rival_data.get("rivals", {})
        if rivals:
            print(f"\n  [竞品] 检索到 {len(rivals)} 个竞品: {', '.join(rivals.keys())}")

        comparison = result.get("comparison", {})
        detailed_report = comparison.get("detailed_report", "") if isinstance(comparison, dict) else ""
        print_report(detailed_report)

        weaknesses = result.get("weaknesses", [])
        if weaknesses:
            print(f"\n  [短板] 发现 {len(weaknesses)} 个短板维度:")
            for w in weaknesses:
                print(f"     - {w.get('维度', '?')}: 本品{w.get('本品评分','?')}分 vs 竞品平均{w.get('竞品平均','?')}分")

        deep_dive = result.get("deep_dive", "")
        print_deep_dive(deep_dive)

        print_thought_chain(result.get("thought_chain", []))


if __name__ == "__main__":
    asyncio.run(main())
