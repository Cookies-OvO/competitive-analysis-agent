<script setup>
import { ref, reactive, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { reportStore } from '../stores/report.js'

const router = useRouter()

const message = ref('')
const analyzing = ref(false)
const rebuilding = ref(false)
const analysisError = ref('')
const rebuildSteps = ref([])
const analysisResult = ref(null)
const rebuildResult = ref('')
const showRebuildModal = ref(false)

// 初始全 done → 显示完整颜色；点按钮后重置为 pending → 逐步激活
const aNode = reactive({
  plan: 'done', self: 'done', rival: 'done',
  aggregate: 'done', deep_dive: 'done', output: 'done',
})
const bNode = reactive({
  loadProducts: 'done', loadModel: 'done',
  rivalBuild: 'done', improveBuild: 'done', clearCache: 'done',
})

// 实时数据（分析）
const aInfo = reactive({
  productName: '', category: '', price: '', dimensions: '', priceRange: '',
  selfCount: '', rivalCount: '',
  scoresSummary: '', weaknessCount: '',
  deepDivePreview: '',
})
// 实时数据（构建）
const bInfo = reactive({
  productCount: '', currentProduct: '', rivalChunks: '', improveChunks: '', modelName: '',
})

// 节点颜色辅助
const aFill = {
  plan:       { pending:'#F9FAFB', active:'#EEF2FF', done:'#EEF2FF' },
  self:       { pending:'#F9FAFB', active:'#EFF6FF', done:'#EFF6FF' },
  rival:      { pending:'#F9FAFB', active:'#ECFDF5', done:'#ECFDF5' },
  aggregate:  { pending:'#F9FAFB', active:'#EEF2FF', done:'#EEF2FF' },
  deep_dive:  { pending:'#F9FAFB', active:'#FFFBEB', done:'#FFFBEB' },
  output:     { pending:'#F9FAFB', active:'#F0FDF4', done:'#F0FDF4' },
}
const aStroke = {
  plan:       { pending:'#E5E7EB', active:'#6366F1', done:'#6366F1' },
  self:       { pending:'#E5E7EB', active:'#3B82F6', done:'#3B82F6' },
  rival:      { pending:'#E5E7EB', active:'#10B981', done:'#10B981' },
  aggregate:  { pending:'#E5E7EB', active:'#6366F1', done:'#6366F1' },
  deep_dive:  { pending:'#E5E7EB', active:'#F59E0B', done:'#D1D5DB' },
  output:     { pending:'#E5E7EB', active:'#10B981', done:'#10B981' },
}
const bFill = {
  loadProducts:  { pending:'#F9FAFB', active:'#EEF2FF', done:'#EEF2FF' },
  loadModel:     { pending:'#F9FAFB', active:'#EEF2FF', done:'#EEF2FF' },
  rivalBuild:    { pending:'#F9FAFB', active:'#ECFDF5', done:'#ECFDF5' },
  improveBuild:  { pending:'#F9FAFB', active:'#FFFBEB', done:'#FFFBEB' },
  clearCache:    { pending:'#F9FAFB', active:'#EEF2FF', done:'#EEF2FF' },
}
const bStroke = {
  loadProducts:  { pending:'#E5E7EB', active:'#6366F1', done:'#6366F1' },
  loadModel:     { pending:'#E5E7EB', active:'#6366F1', done:'#6366F1' },
  rivalBuild:    { pending:'#E5E7EB', active:'#10B981', done:'#10B981' },
  improveBuild:  { pending:'#E5E7EB', active:'#F59E0B', done:'#F59E0B' },
  clearCache:    { pending:'#E5E7EB', active:'#6366F1', done:'#6366F1' },
}
function af(k) { return aFill[k][aNode[k]] }
function as(k) { return aStroke[k][aNode[k]] }
function bf(k) { return bFill[k][bNode[k]] }
function bs(k) { return bStroke[k][bNode[k]] }
const agentMap = { plan_node: 'plan', branch_self_node: 'self', branch_rival_node: 'rival', aggregate_node: 'aggregate', deep_dive_node: 'deep_dive' }

const analysisCard = ref(null)
const rebuildCard = ref(null)

// ---- 分析 ----
async function startAnalysis() {
  if (!message.value.trim() || analyzing.value) return
  analyzing.value = true
  analysisError.value = ''
  analysisResult.value = null
  Object.keys(aInfo).forEach(k => aInfo[k] = '')
  Object.keys(aNode).forEach(k => aNode[k] = 'pending')
  aNode.plan = 'active'
  nextTick(() => { analysisCard.value?.scrollIntoView({ behavior:'smooth', block:'start' }) })

  try {
    const res = await fetch('/api/analyze/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: message.value }),
    })
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    const doneAgents = new Set()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const evt = JSON.parse(line.slice(6))
        if (evt.event === 'thought') {
          const data = evt.data || {}
          const agent = data.agent || ''
          const key = agentMap[agent]
          if (key) { aNode[key] = 'done'; doneAgents.add(key) }

          // 提取实时数据
          if (agent === 'plan_node' && data.output) {
            aInfo.productName = data.output['产品'] || ''
            aInfo.category = data.output['类目'] || ''
            aInfo.price = data.output['价格'] != null ? String(data.output['价格']) : ''
            aInfo.dimensions = Array.isArray(data.output['维度']) ? data.output['维度'].join('、') : ''
            aInfo.priceRange = data.output['价格区间'] || ''
          }
          if (agent === 'branch_self_node' && data.detail) {
            aInfo.selfCount = data.detail
          }
          if (agent === 'branch_rival_node' && data.detail) {
            aInfo.rivalCount = data.detail
          }
          if (agent === 'aggregate_node' && data.output) {
            const scores = data.output.scores || {}
            const dims = Object.keys(scores)
            aInfo.scoresSummary = dims.map(d => `${d}:${scores[d]}`).join(' ')
            aInfo.weaknessCount = data.output.weaknesses != null ? String(data.output.weaknesses) : ''
          }
          if (agent === 'deep_dive_node' && data.output) {
            aInfo.deepDivePreview = typeof data.output === 'string' ? data.output.slice(0, 80) : ''
          }

          // 激活下一阶段
          if (doneAgents.has('plan')) {
            if (!doneAgents.has('self')) aNode.self = 'active'
            if (!doneAgents.has('rival')) aNode.rival = 'active'
          }
          if (doneAgents.has('self') && doneAgents.has('rival')) {
            if (!doneAgents.has('aggregate')) aNode.aggregate = 'active'
          }
          if (doneAgents.has('aggregate')) {
            if (doneAgents.has('deep_dive')) aNode.output = 'active'
          }
          if (doneAgents.has('deep_dive')) aNode.output = 'active'
        } else if (evt.event === 'result') {
          analysisResult.value = evt.data
          reportStore.set(evt.data)
          router.push('/report')
          if (evt.data?.deep_dive) {
            if (!doneAgents.has('deep_dive')) aNode.deep_dive = 'active'
            if (aNode.deep_dive === 'active') aNode.deep_dive = 'done'
          } else {
            aNode.deep_dive = 'done'
          }
          aNode.output = 'done'
        } else if (evt.event === 'error') {
          analysisError.value = evt.data
        }
      }
    }
    Object.keys(aNode).forEach(k => {
      if (aNode[k] === 'active') aNode[k] = 'done'
    })
  } catch (e) {
    analysisError.value = e.message
  } finally {
    analyzing.value = false
    if (aNode.output === 'active') aNode.output = 'done'
    if (!analysisResult.value?.deep_dive) aNode.deep_dive = 'done'
  }
}

// ---- 知识库重建 ----
async function startRebuild() {
  if (rebuilding.value) return
  rebuilding.value = true
  rebuildSteps.value = []
  rebuildResult.value = ''
  showRebuildModal.value = false
  Object.keys(bInfo).forEach(k => bInfo[k] = '')
  Object.keys(bNode).forEach(k => bNode[k] = 'pending')
  nextTick(() => { rebuildCard.value?.scrollIntoView({ behavior:'smooth', block:'start' }) })

  try {
    const res = await fetch('/api/rag/rebuild', { method: 'POST' })
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const s = JSON.parse(line.slice(6))
        rebuildSteps.value.push(s)
        const msg = s.message || ''
        const step = s.step

        // 提取实时数据
        const countMatch = msg.match(/读取到\s*(\d+)\s*款/)
        if (countMatch) bInfo.productCount = countMatch[1]
        const genMatch = msg.match(/生成竞品分析:\s*(.+)/)
        if (genMatch) bInfo.currentProduct = genMatch[1]
        const rivalDone = msg.match(/竞品分析生成完成.*?(\d+)\s*个/)
        if (rivalDone) bInfo.rivalChunks = rivalDone[1]
        const improveDone = msg.match(/改进案例生成完成.*?(\d+)\s*个/)
        if (improveDone) bInfo.improveChunks = improveDone[1]

        if (step === 'loading') {
          if (msg.includes('Embedding') || msg.includes('模型')) { bNode.loadProducts = 'done'; bNode.loadModel = 'active' }
          else if (msg.includes('产品') || msg.includes('读取到')) { bNode.loadProducts = 'active'; bNode.loadModel = 'pending' }
        }
        // 竞品 + 改进案例并行：同时激活 ③ 和 ④
        if (step === 'rival') {
          bNode.loadModel = 'done'
          bNode.rivalBuild = 'active'
          bNode.improveBuild = 'active'
        }
        if (step === 'improve') {
          bNode.loadModel = 'done'
          bNode.rivalBuild = 'active'
          bNode.improveBuild = 'active'
        }
        if (step === 'rival_index') { bNode.rivalBuild = 'done' }
        if (step === 'improve_index') { bNode.improveBuild = 'done' }
        if (step === 'done') {
          bNode.rivalBuild = 'done'
          bNode.improveBuild = 'done'
          bNode.clearCache = 'active'
          setTimeout(() => { bNode.clearCache = 'done' }, 600)
          rebuildResult.value = msg
          showRebuildModal.value = true
        }
      }
    }
  } catch (e) {
    rebuildSteps.value.push({ step: 'error', message: '失败: ' + e.message })
  } finally {
    rebuilding.value = false
    Object.keys(bNode).forEach(k => {
      if (bNode[k] === 'active') bNode[k] = 'done'
    })
  }
}
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>ScopeLens</h1>
        <p style="color:var(--text-secondary);margin-top:4px;font-size:14px;">竞品分析系统</p>
      </div>
    </div>

    <!-- 控制栏 -->
    <div class="card" style="margin-bottom:24px;">
      <div class="card-pad" style="display:flex;align-items:center;gap:12px;padding:16px 24px;">
        <input
          v-model="message"
          placeholder="输入分析需求，例如：帮我分析一下小米手环9 Pro的竞品情况"
          style="flex:1;padding:9px 14px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;font-family:inherit;background:var(--bg);outline:none;"
          :disabled="analyzing || rebuilding"
          @keyup.enter="startAnalysis"
        />
        <button class="btn btn-primary" :disabled="analyzing || rebuilding || !message.trim()" @click="startAnalysis">
          {{ analyzing ? '分析中...' : '开始分析' }}
        </button>
        <button class="btn btn-default" :disabled="analyzing || rebuilding" @click="startRebuild">
          {{ rebuilding ? '构建中...' : '重建知识库' }}
        </button>
      </div>
      <div v-if="analysisError" class="alert alert-error" style="margin:0 24px 16px;">{{ analysisError }}</div>
      <div v-if="rebuildSteps.length" style="padding:0 24px 12px;font-size:12px;max-height:120px;overflow-y:auto;">
        <div
          v-for="(s, i) in rebuildSteps"
          :key="i"
          style="margin-bottom:2px;"
          :style="{ color: s.step === 'error' ? 'var(--red)' : s.step === 'done' ? 'var(--green)' : 'var(--text-secondary)' }"
        >{{ s.step === 'done' ? '✓' : '·' }} {{ s.message }}</div>
      </div>
    </div>

    <!-- 一、分析工作流 -->
    <div ref="analysisCard" class="card" style="margin-bottom:24px;">
      <div class="card-header">
        <h3>分析工作流</h3>
        <span class="pill" :class="analyzing ? 'pill-accent' : (analysisResult ? 'pill-green' : '')" style="font-size:11px;">
          {{ analyzing ? '运行中' : (analysisResult ? '已完成' : '待输入') }}
        </span>
      </div>
      <div class="card-pad" style="display:flex;justify-content:center;padding:16px 0 12px;">
        <svg viewBox="0 0 820 740" style="width:100%;max-width:820px;font-family:inherit;">
          <defs>
            <marker id="a1" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#9CA3AF"/></marker>
            <marker id="a2" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#F59E0B"/></marker>
            <filter id="sd" x="-4%" y="-4%" width="108%" height="116%"><feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.06"/></filter>
            <filter id="glow"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
          </defs>

          <!-- 连线 -->
          <line x1="410" y1="36" x2="410" y2="50" stroke="#9CA3AF" stroke-width="1.5" marker-end="url(#a1)"/>
          <polyline points="410,108 410,138 180,138 180,160" fill="none" stroke="#9CA3AF" stroke-width="1.5" marker-end="url(#a1)"/>
          <polyline points="410,108 410,138 640,138 640,160" fill="none" stroke="#9CA3AF" stroke-width="1.5" marker-end="url(#a1)"/>
          <polyline points="180,220 180,242 410,242 410,270" fill="none" stroke="#9CA3AF" stroke-width="1.5" marker-end="url(#a1)"/>
          <polyline points="640,220 640,242 410,242" fill="none" stroke="#9CA3AF" stroke-width="1.5"/>
          <line x1="410" y1="332" x2="410" y2="348" stroke="#9CA3AF" stroke-width="1.5" marker-end="url(#a1)"/>
          <line x1="410" y1="425" x2="410" y2="648" stroke="#D1D5DB" stroke-width="1.5" marker-end="url(#a1)" stroke-dasharray="5,3"/>
          <polyline points="475,387 507,387 507,531 528,531" fill="none" stroke="#F59E0B" stroke-width="1.8" marker-end="url(#a2)"/>
          <polyline points="660,578 660,610 410,610 410,648" fill="none" stroke="#9CA3AF" stroke-width="1.5" marker-end="url(#a1)"/>

          <!-- 用户输入 -->
          <rect x="300" y="14" width="220" height="22" rx="11" fill="#F3F4F6" stroke="#E5E7EB" stroke-width="1"/>
          <text x="410" y="29" text-anchor="middle" font-size="11" fill="#6B7280">{{ message || '用户输入分析需求' }}</text>

          <!-- ① plan -->
          <rect x="130" y="50" width="560" height="58" rx="8" :fill="af('plan')" :stroke="as('plan')" stroke-width="1.5" :filter="aNode.plan==='active' ? 'url(#glow)' : 'url(#sd)'"/>
          <text x="410" y="69" text-anchor="middle" font-size="13" font-weight="700" :fill="aNode.plan==='pending' ? '#D1D5DB' : '#4F46E5'">① plan_node</text>
          <text x="410" y="87" text-anchor="middle" font-size="11" :fill="aNode.plan==='pending' ? '#D1D5DB' : '#4B5563'">
            <tspan v-if="aInfo.productName">LLM 解析 → 本品: {{ aInfo.productName }} / {{ aInfo.category }} / ¥{{ aInfo.price }} / 维度: {{ aInfo.dimensions }}</tspan>
            <tspan v-else>LLM 解析 + DB 匹配 → product_id / category / dimensions / price_range</tspan>
          </text>
          <text x="410" y="103" text-anchor="middle" font-size="10.5" :fill="aNode.plan==='pending' ? '#D1D5DB' : '#6B7280'">
            <tspan v-if="aInfo.priceRange">价位: {{ aInfo.priceRange }}</tspan>
            <tspan v-else>temperature=0.1 / response_format=JSON</tspan>
          </text>

          <text x="410" y="150" text-anchor="middle" font-size="10" fill="#9CA3AF">两路并行 (LangGraph 自动并发)</text>

          <!-- ② self -->
          <rect x="40" y="160" width="280" height="60" rx="8" :fill="af('self')" :stroke="as('self')" stroke-width="1.5" :filter="aNode.self==='active' ? 'url(#glow)' : 'url(#sd)'"/>
          <text x="180" y="179" text-anchor="middle" font-size="13" font-weight="700" :fill="aNode.self==='pending' ? '#D1D5DB' : '#2563EB'">② branch_self_node</text>
          <text x="180" y="197" text-anchor="middle" font-size="11" :fill="aNode.self==='pending' ? '#D1D5DB' : '#4B5563'">
            <tspan v-if="aInfo.selfCount">{{ aInfo.selfCount }}</tspan>
            <tspan v-else>DB: reviews + review_tags 表 LEFT JOIN</tspan>
          </text>
          <text x="180" y="213" text-anchor="middle" font-size="10.5" :fill="aNode.self==='pending' ? '#D1D5DB' : '#6B7280'">按维度聚合 → avg_rating / 正负标签 / 样本评论</text>

          <!-- ③ rival -->
          <rect x="500" y="160" width="280" height="60" rx="8" :fill="af('rival')" :stroke="as('rival')" stroke-width="1.5" :filter="aNode.rival==='active' ? 'url(#glow)' : 'url(#sd)'"/>
          <text x="640" y="179" text-anchor="middle" font-size="13" font-weight="700" :fill="aNode.rival==='pending' ? '#D1D5DB' : '#059669'">③ branch_rival_node</text>
          <text x="640" y="197" text-anchor="middle" font-size="11" :fill="aNode.rival==='pending' ? '#D1D5DB' : '#4B5563'">
            <tspan v-if="aInfo.rivalCount">{{ aInfo.rivalCount }}</tspan>
            <tspan v-else>FAISS RAG: faiss_rival/ 向量检索 (top_k=10)</tspan>
          </text>
          <text x="640" y="213" text-anchor="middle" font-size="10.5" :fill="aNode.rival==='pending' ? '#D1D5DB' : '#6B7280'">query="{品类} {价位} 竞品" → 按竞品名 &amp; 维度分组</text>



<!-- ④ aggregate -->
          <rect x="130" y="270" width="560" height="60" rx="8" :fill="af('aggregate')" :stroke="as('aggregate')" stroke-width="1.5" :filter="aNode.aggregate==='active' ? 'url(#glow)' : 'url(#sd)'"/>
          <text x="410" y="290" text-anchor="middle" font-size="13" font-weight="700" :fill="aNode.aggregate==='pending' ? '#D1D5DB' : '#4F46E5'">④ aggregate_node</text>
          <text x="410" y="308" text-anchor="middle" font-size="11" :fill="aNode.aggregate==='pending' ? '#D1D5DB' : '#4B5563'">
            <tspan v-if="aInfo.scoresSummary">维度评分: {{ aInfo.scoresSummary }}  |  短板: {{ aInfo.weaknessCount }}个</tspan>
            <tspan v-else>LLM (aggregate_prompt.txt, temperature=0.1, response_format=JSON)</tspan>
          </text>
          <text x="410" y="324" text-anchor="middle" font-size="10.5" :fill="aNode.aggregate==='pending' ? '#D1D5DB' : '#6B7280'">输出 → dimension_scores / strengths / weaknesses / conclusion</text>

          <!-- 决策菱形 -->
          <polygon points="410,348 480,387 410,426 340,387" fill="#F9FAFB" stroke="#D1D5DB" stroke-width="1.5"/>
          <text x="410" y="383" text-anchor="middle" font-size="10" fill="#6B7280">should_deep_dive?</text>
          <text x="410" y="398" text-anchor="middle" font-size="10" fill="#6B7280">本品评分 &lt; 60 ?</text>
          <text x="393" y="490" text-anchor="end" font-size="11" fill="#9CA3AF">否 → 所有维度 ≥ 60 分</text>
          <text x="482" y="382" text-anchor="start" font-size="11" fill="#F59E0B" font-weight="600">是 → 任一维度 &lt; 60 分</text>

          <!-- ⑤ deep_dive -->
          <rect x="528" y="485" width="264" height="93" rx="8" :fill="af('deep_dive')" :stroke="as('deep_dive')" stroke-width="1.5" :filter="aNode.deep_dive==='active' ? 'url(#glow)' : 'url(#sd)'"/>
          <text x="660" y="504" text-anchor="middle" font-size="13" font-weight="700" :fill="aNode.deep_dive==='pending' ? '#D1D5DB' : '#D97706'">⑤ deep_dive_node</text>
          <text x="660" y="523" text-anchor="middle" font-size="10.5" :fill="aNode.deep_dive==='pending' ? '#D1D5DB' : '#6B7280'">
            <tspan v-if="aInfo.deepDivePreview">{{ aInfo.deepDivePreview }}</tspan>
            <tspan v-else>每个低分维度分别执行：</tspan>
          </text>
          <text x="660" y="541" text-anchor="middle" font-size="10" :fill="aNode.deep_dive==='pending' ? '#D1D5DB' : '#4B5563'">① DB: SELECT 该维度 ≤2 星差评 (LIMIT 5)</text>
          <text x="660" y="558" text-anchor="middle" font-size="10" :fill="aNode.deep_dive==='pending' ? '#D1D5DB' : '#4B5563'">② RAG: faiss_improve/ 检索改进案例 (top_k=3)</text>
          <text x="660" y="575" text-anchor="middle" font-size="10" :fill="aNode.deep_dive==='pending' ? '#D1D5DB' : '#4B5563'">③ LLM: 综合差评+案例 → Markdown 改进方案</text>

          <!-- 输出 -->
          <rect x="240" y="648" width="340" height="58" rx="8" :fill="af('output')" :stroke="as('output')" stroke-width="1.5" :filter="aNode.output==='active' ? 'url(#glow)' : 'url(#sd)'"/>
          <text x="410" y="668" text-anchor="middle" font-size="13" font-weight="700" :fill="aNode.output==='pending' ? '#D1D5DB' : '#059669'">生成 Markdown 报告</text>
          <text x="410" y="686" text-anchor="middle" font-size="11" :fill="aNode.output==='pending' ? '#D1D5DB' : '#4B5563'">汇总 comparison + deep_dive → 持久化到 reports 表</text>
          <text x="410" y="702" text-anchor="middle" font-size="10.5" :fill="aNode.output==='pending' ? '#D1D5DB' : '#6B7280'">同步推送 SSE 流式更新 (astream_events)</text>

          <!-- 图例 -->
          <rect x="24" y="718" width="10" height="10" rx="2" fill="#3B82F6"/><text x="38" y="727" font-size="10" fill="#6B7280">DB (SQLite)</text>
          <rect x="115" y="718" width="10" height="10" rx="2" fill="#10B981"/><text x="129" y="727" font-size="10" fill="#6B7280">RAG (FAISS)</text>
          <rect x="220" y="718" width="10" height="10" rx="2" fill="#6366F1"/><text x="234" y="727" font-size="10" fill="#6B7280">LLM (DeepSeek)</text>
          <rect x="350" y="718" width="10" height="10" rx="2" fill="#F59E0B"/><text x="364" y="727" font-size="10" fill="#6B7280">条件路由</text>
          <text x="450" y="727" font-size="10" fill="#9CA3AF">DEEP_DIVE_THRESHOLD = 60 (可配置)</text>
        </svg>
      </div>
    </div>

    <!-- 二、知识库构建流程 -->
    <div ref="rebuildCard" class="card" style="margin-bottom:24px;">
      <div class="card-header">
        <h3>知识库构建流程</h3>
        <span class="pill" :class="rebuilding ? 'pill-accent' : (bNode.clearCache==='done' ? 'pill-green' : '')" style="font-size:11px;">
          {{ rebuilding ? '构建中' : (bNode.clearCache==='done' ? '已就绪' : '空闲') }}
        </span>
      </div>
      <div class="card-pad" style="display:flex;justify-content:center;padding:16px 0 10px;">
        <svg viewBox="0 0 820 370" style="width:100%;max-width:820px;font-family:inherit;">
          <defs>
            <marker id="b1" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#9CA3AF"/></marker>
            <filter id="sd2" x="-4%" y="-4%" width="108%" height="116%"><feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.06"/></filter>
            <filter id="glow2"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
          </defs>

          <!-- 连线 -->
          <line x1="410" y1="56" x2="410" y2="78" stroke="#9CA3AF" stroke-width="1.5" marker-end="url(#b1)"/>
          <polyline points="410,122 410,148 180,148 180,171" fill="none" stroke="#9CA3AF" stroke-width="1.5" marker-end="url(#b1)"/>
          <polyline points="410,122 410,148 640,148 640,171" fill="none" stroke="#9CA3AF" stroke-width="1.5" marker-end="url(#b1)"/>
          <polyline points="180,262 180,294 410,294 410,314" fill="none" stroke="#9CA3AF" stroke-width="1.5" marker-end="url(#b1)"/>
          <polyline points="640,262 640,294 410,294" fill="none" stroke="#9CA3AF" stroke-width="1.5"/>

          <!-- ① -->
          <rect x="310" y="18" width="200" height="38" rx="8" :fill="bf('loadProducts')" :stroke="bs('loadProducts')" stroke-width="1.5" :filter="bNode.loadProducts==='active' ? 'url(#glow2)' : 'url(#sd2)'"/>
          <text x="410" y="34" text-anchor="middle" font-size="12" font-weight="700" :fill="bNode.loadProducts==='pending' ? '#D1D5DB' : '#4F46E5'">① 读取产品数据</text>
          <text x="410" y="49" text-anchor="middle" font-size="10" :fill="bNode.loadProducts==='pending' ? '#D1D5DB' : '#6B7280'">
            <tspan v-if="bInfo.productCount">DB: SELECT * FROM products → {{ bInfo.productCount }} 款产品</tspan>
            <tspan v-else>DB: SELECT * FROM products</tspan>
          </text>

          <!-- ② -->
          <rect x="280" y="78" width="260" height="44" rx="8" :fill="bf('loadModel')" :stroke="bs('loadModel')" stroke-width="1.5" :filter="bNode.loadModel==='active' ? 'url(#glow2)' : 'url(#sd2)'"/>
          <text x="410" y="96" text-anchor="middle" font-size="12" font-weight="700" :fill="bNode.loadModel==='pending' ? '#D1D5DB' : '#4F46E5'">② 加载 Embedding 模型</text>
          <text x="410" y="113" text-anchor="middle" font-size="10" :fill="bNode.loadModel==='pending' ? '#D1D5DB' : '#6B7280'">BAAI/bge-small-zh-v1.5</text>

          <text x="410" y="160" text-anchor="middle" font-size="10" fill="#9CA3AF">两路并行 (ThreadPoolExecutor, max_workers=2)</text>

          <!-- ③ -->
          <rect x="20" y="172" width="380" height="90" rx="8" :fill="bf('rivalBuild')" :stroke="bs('rivalBuild')" stroke-width="1.5" :filter="bNode.rivalBuild==='active' ? 'url(#glow2)' : 'url(#sd2)'"/>
          <text x="210" y="191" text-anchor="middle" font-size="12" font-weight="700" :fill="bNode.rivalBuild==='pending' ? '#D1D5DB' : '#059669'">③ 竞品向量索引</text>
          <text x="210" y="213" text-anchor="middle" font-size="10" :fill="bNode.rivalBuild==='pending' ? '#D1D5DB' : '#4B5563'">
            <tspan v-if="bInfo.currentProduct && bNode.rivalBuild!=='done'">正在: {{ bInfo.currentProduct }}</tspan>
            <tspan v-else-if="bInfo.rivalChunks">已生成 {{ bInfo.rivalChunks }} 个文本块</tspan>
            <tspan v-else>每个产品 → LLM (RIVAL_PROMPT, temp=0.3) → 按 ## 切分 → 向量化</tspan>
          </text>
          <text x="210" y="232" text-anchor="middle" font-size="10" :fill="bNode.rivalBuild==='pending' ? '#D1D5DB' : '#4B5563'">FAISS IndexFlatIP (内积) → normalize_embeddings=True</text>
          <text x="210" y="251" text-anchor="middle" font-size="10" :fill="bNode.rivalBuild==='pending' ? '#D1D5DB' : '#6B7280'">→ data/faiss_rival/ (index.faiss + chunks.json)</text>

          <!-- ④ -->
          <rect x="420" y="172" width="380" height="90" rx="8" :fill="bf('improveBuild')" :stroke="bs('improveBuild')" stroke-width="1.5" :filter="bNode.improveBuild==='active' ? 'url(#glow2)' : 'url(#sd2)'"/>
          <text x="610" y="191" text-anchor="middle" font-size="12" font-weight="700" :fill="bNode.improveBuild==='pending' ? '#D1D5DB' : '#D97706'">④ 改进案例向量索引</text>
          <text x="610" y="213" text-anchor="middle" font-size="10" :fill="bNode.improveBuild==='pending' ? '#D1D5DB' : '#4B5563'">
            <tspan v-if="bInfo.improveChunks">已生成 {{ bInfo.improveChunks }} 个文本块</tspan>
            <tspan v-else>每个品类去重 → LLM (IMPROVE_PROMPT, temp=0.3) → 按 ## 切分 → 向量化</tspan>
          </text>
          <text x="610" y="232" text-anchor="middle" font-size="10" :fill="bNode.improveBuild==='pending' ? '#D1D5DB' : '#4B5563'">FAISS IndexFlatIP (内积) → normalize_embeddings=True</text>
          <text x="610" y="251" text-anchor="middle" font-size="10" :fill="bNode.improveBuild==='pending' ? '#D1D5DB' : '#6B7280'">→ data/faiss_improve/ (index.faiss + chunks.json)</text>

          <!-- ⑤ -->
          <rect x="300" y="314" width="220" height="38" rx="8" :fill="bf('clearCache')" :stroke="bs('clearCache')" stroke-width="1.5" :filter="bNode.clearCache==='active' ? 'url(#glow2)' : 'url(#sd2)'"/>
          <text x="410" y="331" text-anchor="middle" font-size="12" font-weight="700" :fill="bNode.clearCache==='pending' ? '#D1D5DB' : '#4F46E5'">⑤ 清除检索缓存</text>
          <text x="410" y="346" text-anchor="middle" font-size="10" :fill="bNode.clearCache==='pending' ? '#D1D5DB' : '#6B7280'">retrieve._index_cache.clear()</text>
        </svg>
      </div>
    </div>

    <!-- 知识库重建结果弹窗 -->
    <div v-if="showRebuildModal" class="modal-overlay" @click.self="showRebuildModal = false">
      <div class="modal" style="width:440px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
          <h3 style="margin:0;">知识库重建完成</h3>
          <button class="btn btn-ghost btn-sm" @click="showRebuildModal = false">关闭</button>
        </div>
        <div style="text-align:center;padding:8px 0;">
          <p style="font-size:15px;color:var(--green);font-weight:600;margin-bottom:16px;">{{ rebuildResult }}</p>
          <div v-if="bInfo.productCount" style="font-size:13px;color:var(--text-secondary);margin-bottom:4px;">产品数: {{ bInfo.productCount }} 款</div>
          <div v-if="bInfo.rivalChunks" style="font-size:13px;color:var(--text-secondary);margin-bottom:4px;">竞品文本块: {{ bInfo.rivalChunks }} 个</div>
          <div v-if="bInfo.improveChunks" style="font-size:13px;color:var(--text-secondary);margin-bottom:4px;">改进案例块: {{ bInfo.improveChunks }} 个</div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-primary btn-sm" @click="showRebuildModal = false">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>
