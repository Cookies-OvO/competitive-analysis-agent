<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { reportStore } from '../stores/report.js'

const router = useRouter()

function parseReport(md) {
  if (!md) return []
  const sections = []
  const lines = md.split('\n')
  let current = null
  let tableRows = []
  let tableHeader = []

  function flushCurrent() {
    if (!current) return
    if (tableRows.length) {
      current.table = { header: tableHeader, rows: tableRows }
      tableRows = []
      tableHeader = []
    }
    sections.push(current)
    current = null
  }

  for (const line of lines) {
    // section header (###)
    if (line.startsWith('### ')) {
      flushCurrent()
      current = { title: line.replace(/^###\s*/, ''), items: [], table: null }
      continue
    }
    // sub-heading (####) → render as bold label within items
    if (line.startsWith('#### ')) {
      if (current) {
        current.items.push({ sub: line.replace(/^####\s*/, '') })
      }
      continue
    }
    if (!current) continue

    // table separator (skip)
    if (/^\|[-|\s]+\|$/.test(line.trim())) continue

    // table row
    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
      const cells = line.split('|').filter(c => c.trim() !== '').map(c => c.trim())
      if (!current.table && !tableHeader.length) {
        tableHeader = cells
      } else {
        tableRows.push(cells)
      }
      continue
    }

    // list items
    const liMatch = line.match(/^[-*]\s+(.+)/)
    const olMatch = line.match(/^\d+\.\s+(.+)/)
    if (liMatch || olMatch) {
      const text = (liMatch || olMatch)[1]
      current.items.push({ text: parseBold(text) })
      continue
    }

    // plain text (skip empty)
    const trimmed = line.trim()
    if (trimmed) {
      current.items.push({ text: parseBold(trimmed) })
    }
  }
  flushCurrent()
  return sections
}

function parseBold(text) {
  return text.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
}

// 从 comparison_report 中提取各段
const sections = computed(() => parseReport(reportStore.comparisonReport))
const deepDiveSections = computed(() => parseReport(reportStore.deepDive))

const weaknesses = computed(() => reportStore.weaknesses || [])
const hasDeepDive = computed(() => !!reportStore.deepDive)

// 判断单元格是否为正值（含 + 号）
function isPositive(val) {
  return val && (val.startsWith('+') || /优势|优于|领先|突出|更强|好于/.test(val))
}
function isNegative(val) {
  return val && (val.startsWith('-') || /短板|不足|落后|逊色|弱于|需提升/.test(val))
}
function cellClass(val, ci) {
  if (ci === 0) return ''
  if (isPositive(val)) return 'cell-good'
  if (isNegative(val)) return 'cell-bad'
  return ''
}
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>分析报告</h1>
        <p style="color:var(--text-secondary);margin-top:4px;font-size:14px;">
          <span class="pill pill-accent">{{ reportStore.productName }}</span>
        </p>
      </div>
      <button class="btn btn-ghost" @click="router.push('/')">← 返回首页</button>
    </div>

    <!-- 短板维度卡片 -->
    <div v-if="weaknesses.length" class="card" style="margin-bottom:20px;">
      <div class="card-header"><h3>短板概览</h3></div>
      <div class="card-pad" style="display:flex;flex-wrap:wrap;gap:12px;">
        <div
          v-for="(w, i) in weaknesses"
          :key="i"
          style="background:var(--red-light);border:1px solid rgba(239,68,68,.15);border-radius:var(--radius-lg);padding:14px 18px;flex:1;min-width:160px;"
        >
          <div style="font-size:13px;font-weight:600;margin-bottom:6px;">{{ w.维度 || w.dimension }}</div>
          <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:4px;">
            <span style="font-size:24px;font-weight:700;color:var(--red);">{{ w.本品评分 || w.score }}</span>
            <span style="font-size:12px;color:var(--text-muted);">本品得分</span>
          </div>
          <div v-if="(w.竞品平均 || w.rival_avg) != null" style="font-size:12px;color:var(--text-secondary);margin-bottom:2px;">
            竞品平均 {{ w.竞品平均 || w.rival_avg }} 分
            <span v-if="(w.差距 || w.gap) != null" style="color:var(--red);">（落后 {{ w.差距 || w.gap }} 分）</span>
          </div>
          <div v-if="w.描述 || w.desc" style="font-size:11px;color:var(--text-muted);margin-top:4px;">{{ w.描述 || w.desc }}</div>
        </div>
      </div>
    </div>

    <!-- 报告正文（循环渲染 section） -->
    <div v-for="(sec, si) in sections" :key="si" class="card" style="margin-bottom:20px;">
      <div class="card-header"><h3>{{ sec.title }}</h3></div>
      <div class="card-pad">
        <!-- 表格 -->
        <template v-if="sec.table">
          <table>
            <thead>
              <tr>
                <th v-for="(h, hi) in sec.table.header" :key="hi">{{ h }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, ri) in sec.table.rows" :key="ri">
                <td
                  v-for="(cell, ci) in row"
                  :key="ci"
                  :class="cellClass(cell, ci)"
                >
                  <span v-if="cellClass(cell, ci)" class="pill" :class="isPositive(cell) ? 'pill-green' : 'pill-red'" style="margin-right:4px;">{{ cell }}</span>
                  <span v-else-if="ci === 0" style="font-weight:500;">{{ cell }}</span>
                  <span v-else v-html="cell"></span>
                </td>
              </tr>
            </tbody>
          </table>
        </template>
        <!-- 列表 -->
        <template v-if="sec.items.length">
          <div v-for="(item, ii) in sec.items" :key="ii" style="padding:8px 0;border-bottom:1px solid var(--border);font-size:14px;line-height:1.7;" :style="ii === sec.items.length - 1 ? 'border-bottom:none;' : ''">
            <template v-if="item.sub">
              <span style="font-weight:700;color:var(--text);font-size:13px;">{{ item.sub }}</span>
            </template>
            <template v-else>
              <span v-html="item.text || item"></span>
            </template>
          </div>
        </template>
      </div>
    </div>

    <!-- 深挖建议 -->
    <div v-if="hasDeepDive" class="card" style="margin-bottom:20px;border-color:rgba(245,158,11,.3);">
      <div class="card-header" style="background:var(--amber-light);"><h3>深挖改进建议</h3></div>
      <div class="card-pad">
        <template v-for="(sec, si) in deepDiveSections" :key="'dd'+si">
          <h4 v-if="sec.title" style="font-size:14px;font-weight:600;margin-bottom:8px;color:var(--text);">{{ sec.title }}</h4>
          <div v-for="(item, ii) in sec.items" :key="ii" style="padding:6px 0;font-size:14px;line-height:1.7;border-bottom:1px solid var(--border);" :style="ii === sec.items.length - 1 ? 'border-bottom:none;' : ''">
            <template v-if="item.sub">
              <span style="font-weight:700;color:var(--text);font-size:13px;">{{ item.sub }}</span>
            </template>
            <template v-else>
              <span v-html="item.text || item"></span>
            </template>
          </div>
        </template>
      </div>
    </div>

    <!-- 空态 -->
    <div v-if="!sections.length && !weaknesses.length && !hasDeepDive" class="empty">
      <p>暂无报告数据</p>
      <button class="btn btn-primary" style="margin-top:16px;" @click="router.push('/')">去分析</button>
    </div>
  </div>
</template>

<style scoped>
.cell-good { color: var(--green); font-weight: 600; }
.cell-bad  { color: var(--red);  font-weight: 600; }
</style>
