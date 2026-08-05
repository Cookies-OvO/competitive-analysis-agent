# 竞品分析 Agent 系统

基于 **LangGraph** 的多 Agent 竞品分析系统，输入产品名，自动拉取本品评价 + RAG 检索竞品情报 + LLM 多维度对比分析 + 短板深挖建议。

---

## 架构图

```
用户输入 "分析一下运动手环9pro的竞品表现"
        │
        ▼
  ① plan_node       → LLM 确定产品 + 维度 + 价位 (DB products)
        │
   ┌────┴────┐      → 两路并行（operator.add reducer 合并状态）
   ▼         ▼
② self    ③ rival
   │         │
   DB        FAISS (LLM 动态生成竞品知识)
   └────┬────┘
        ▼
④ aggregate_node    → LLM 多维度对比打分
        │
        ▼
  should_deep_dive?（任一维度本品评分 < 60，阈值可通过 DEEP_DIVE_THRESHOLD 配置）
   │           │
 (否)        (是)
   │           ▼
   │    ⑤ deep_dive  → DB 差评 + FAISS 改进案例 + LLM
   │           │
   └─────┬─────┘
         ▼
   生成 Markdown 报告 → 持久化 reports 表
```

### State 流转

每个节点写入和读取的字段：

| 节点 | 读取 | 写入 |
|------|------|------|
| plan_node | `user_message` | `product_id`, `product_name`, `product_category`, `price_range`, `dimensions` |
| branch_self_node | `product_id`, `dimensions` | `self_summary` |
| branch_rival_node | `product_category`, `price_range`, `dimensions` | `rival_summary` |
| aggregate_node | `product_name`, `self_summary`, `rival_summary` | `comparison`, `weaknesses` |
| deep_dive_node | `product_name`, `weaknesses` | `deep_dive` |

所有节点都会往 `thought_chain` 追加记录，由于 `self` 和 `rival` 并行执行，`thought_chain` 使用 `Annotated[list, operator.add]` reducer 保证追加而非覆盖。

---

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

在 `backend/` 下创建 `.env` 文件：

```bash
LLM_API_KEY=your_api_key        # 必填
LLM_BASE_URL=https://api.deepseek.com/v1  # 可选，默认 DeepSeek
LLM_MODEL=deepseek-chat         # 可选
DEEP_DIVE_THRESHOLD=60          # 可选，深挖触发阈值（满分 100）
```

支持任意 OpenAI 兼容接口（OpenAI、通义千问、硅基流动等）。

### 3. 初始化数据 & 构建知识库

通过前端页面（`/products`、`/reviews`）添加产品和评价后，构建 FAISS 向量索引：

```bash
# API 方式（支持 SSE 进度推送）
curl -X POST http://localhost:8000/api/rag/rebuild

# 或 CLI 构建
python -m app.rag.build_index
```

> **RAG 知识库生成原理**：`build_index.py` 用 LLM 为每个产品生成竞品市场报告和改进案例，通过 `BAAI/bge-small-zh-v1.5` 向量化后存入 FAISS，而非从网络爬取。首次运行会自动从 HuggingFace 下载 embedding 模型（国内可设 `HF_ENDPOINT=https://hf-mirror.com` 加速）。

### 4. 启动服务

```bash
# 后端
cd backend
python -m app.main          # http://localhost:8000

# 前端（新终端）
cd frontend
npm install && npm run dev  # http://localhost:5173
```

浏览器打开 `http://localhost:5173` 使用前端页面，`http://localhost:8000/docs` 查看 API 文档。

### CLI 模式

不启动前端也能用命令行交互：

```bash
cd backend
python -m app.cli
```

输入产品名称即可开始分析，输入 `/quit` 退出。

---

## API 端点

### `POST /api/analyze` — 同步分析

请求：

```json
{"message": "分析一下运动手环9pro的竞品表现"}
```

响应：

```json
{
  "product_name": "运动手环9pro",
  "comparison_report": "## 概述\n...",
  "weaknesses": [{"维度": "续航", "本品评分": 45, "竞品平均": 72}],
  "deep_dive": "### 一、问题根因分析\n...",
  "thought_chain": [{"agent": "plan_node", "status": "completed", ...}]
}
```

### `POST /api/analyze/stream` — SSE 流式分析

同上请求体，返回 SSE 事件流：`thought`（增量推送思考链）→ `result`（最终报告）→ `done`。

### `POST /api/rag/rebuild` — 重建知识库

SSE 流式返回构建进度。每次添加新产品或评价后需要调用。

### 其他 CRUD 接口

`/api/products`、`/api/reviews`、`/api/review_tags`、`/api/reports` — 详见 `/docs`。

---

## 技术栈

| 组件 | 技术 |
|------|------|
| Agent 框架 | LangGraph (StateGraph + 条件边 + 并行分支) |
| LLM | OpenAI 兼容 API (DeepSeek Chat) |
| 后端 | FastAPI + SSE 流式推送 |
| 前端 | Vue 3 + Vite |
| 数据库 | SQLAlchemy 2.0 + SQLite (可切换 PostgreSQL) |
| RAG | FAISS + sentence-transformers (BAAI/bge-small-zh-v1.5) |

---

## 运行测试

```bash
cd backend
pytest tests/ -v
```

---

## 项目结构

```
competitive-analysis-agent/
├── backend/
│   ├── app/
│   │   ├── config.py              # 全局配置（pydantic-settings）
│   │   ├── state.py               # AgentState 定义 + operator.add reducer
│   │   ├── graph.py               # LangGraph 工作流编排 + 条件路由
│   │   ├── agents_llm.py          # LLM 调用封装（OpenAI SDK）
│   │   ├── main.py                # FastAPI 入口 + /api/analyze
│   │   ├── cli.py                 # CLI 交互入口
│   │   ├── schemas.py             # Pydantic 请求/响应模型
│   │   ├── api/                   # REST API 路由
│   │   │   ├── products.py
│   │   │   ├── reviews.py
│   │   │   ├── review_tags.py
│   │   │   ├── reports.py
│   │   │   └── rag.py             # 知识库重建接口
│   │   ├── db/                    # 数据库层
│   │   │   ├── engine.py          # 异步 SQLAlchemy 引擎
│   │   │   └── models.py          # ORM: Product, Review, ReviewTag, Report
│   │   ├── rag/                   # RAG 检索层
│   │   │   ├── build_index.py     # FAISS 索引构建（LLM 生成知识）
│   │   │   └── retrieve.py        # 在线向量检索（缓存加载）
│   │   ├── tools/                 # 工具函数（节点直接调用，非 tool-calling）
│   │   │   ├── get_product_info.py
│   │   │   ├── query_reviews.py
│   │   │   ├── search_rival.py
│   │   │   └── save_report.py
│   │   ├── nodes/                 # LangGraph 节点
│   │   │   ├── plan_node.py       # ① LLM 规划：产品匹配 + 维度选择
│   │   │   ├── branch_self_node.py # ② 本品评价聚合（DB 查询）
│   │   │   ├── branch_rival_node.py # ③ 竞品情报检索（FAISS）
│   │   │   ├── aggregate_node.py  # ④ 多维度对比打分
│   │   │   └── deep_dive_node.py  # ⑤ 短板深挖 + 改进建议
│   │   └── prompts/               # Prompt 模板（独立 .txt 文件）
│   │       ├── plan_prompt.txt
│   │       ├── aggregate_prompt.txt
│   │       └── deep_dive_prompt.txt
│   ├── data/
│   │   ├── products.db            # SQLite 数据库
│   │   ├── faiss_rival/           # 竞品知识 FAISS 索引
│   │   └── faiss_improve/         # 改进案例 FAISS 索引
│   └── tests/
│       ├── test_graph.py          # LangGraph 集成测试
│       └── test_tools.py          # 工具函数单元测试
└── frontend/
    ├── src/
    │   ├── views/
    │   │   ├── Home.vue           # 首页（分析入口 + 知识库构建）
    │   │   ├── Products.vue       # 产品管理
    │   │   ├── Reviews.vue        # 评价管理
    │   │   ├── Report.vue         # 分析报告展示
    │   │   └── Reports.vue        # 历史报告列表
    │   ├── api/index.js           # API 封装
    │   ├── stores/report.js       # 报告状态共享
    │   └── router/index.js        # 路由配置
    └── vite.config.js
```
