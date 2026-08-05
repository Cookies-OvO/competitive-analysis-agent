# 竞品分析 Agent — 前端

Vue 3 + Vite SPA 单页应用，配合后端 FastAPI 提供竞品分析系统的前端界面。

## 技术栈

- Vue 3 (Composition API + `<script setup>`)
- Vue Router 4
- Vite 5

## 项目结构

```
src/
├── main.js              # 应用入口
├── App.vue              # 根组件 (侧边栏导航)
├── style.css            # 全局样式 (CSS 变量主题)
├── api/
│   └── index.js         # 后端 API 封装 (fetch 基类)
├── router/
│   └── index.js         # 路由: / /reports /report /products /products/:id
├── stores/
│   └── report.js        # 分析结果临时存储 (分析完成 → 跳转报告页)
└── views/
    ├── Home.vue         # 首页: 分析输入 + 工作流 SVG + 知识库构建
    ├── Report.vue       # 报告展示: Markdown 解析渲染 (表格/标签/弱点卡片)
    ├── Reports.vue      # 历史报告: 列表筛选 + 弹窗查看 + MD 导出 + 删除
    ├── Products.vue     # 产品管理: CRUD 表格
    ├── Reviews.vue      # 评价管理: 按产品筛选的标签化评价列表
    └── Analyze.vue      # 遗留分析页 (保留兼容)
```

## 开发

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # 生产构建到 dist/
```

前端默认请求 `/api/*` 到同源后端。开发时通过 `vite.config.js` 中的 proxy 配置转发到 `http://localhost:8000`。

## 视图说明

| 路由 | 视图 | 功能 |
|------|------|------|
| `/` | Home.vue | 输入产品名发起分析（SSE 流式），查看工作流 SVG，触发知识库重建 |
| `/report` | Report.vue | 展示分析报告：Markdown 解析、表格标签渲染、维度评分条、弱点卡片、深挖建议 |
| `/reports` | Reports.vue | 历史报告列表（按产品筛选）、查看弹窗、Markdown 导出、确认删除 |
| `/products` | Products.vue | 产品 CRUD |
| `/products/:id` | Reviews.vue | 某产品的评价管理（含标签 CRUD） |
