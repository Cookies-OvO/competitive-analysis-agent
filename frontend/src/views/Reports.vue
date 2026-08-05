<script setup>
import { ref, onMounted } from 'vue'
import { getProducts, getReports, deleteReport } from '../api'

const products = ref([])
const reports = ref([])
const loading = ref(false)
const filterProductId = ref('')
const viewReport = ref(null)
const confirmId = ref(null)

async function load() {
  loading.value = true
  try {
    reports.value = await getReports(filterProductId.value || undefined)
  } catch (e) { /* ignore */ }
  loading.value = false
}

async function doDelete(id) {
  try {
    await deleteReport(id)
    reports.value = reports.value.filter(r => r.id !== id)
    if (viewReport.value?.id === id) viewReport.value = null
  } catch (e) {
    alert('删除失败: ' + (e.message || '未知错误'))
  }
  confirmId.value = null
}

function openReport(r) {
  viewReport.value = r
}

function exportMd() {
  if (!viewReport.value) return
  const r = viewReport.value
  const parts = []
  parts.push(`# 产品 #${r.product_id} 分析报告`)
  parts.push(`> 生成时间: ${r.created_at}`)
  parts.push('')
  if (r.comparison?.conclusion) {
    parts.push(`**结论**：${r.comparison.conclusion}`)
    parts.push('')
  }
  if (r.comparison?.dimension_scores) {
    parts.push('## 维度评分')
    for (const [k, v] of Object.entries(r.comparison.dimension_scores)) {
      parts.push(`- **${k}**：${v} 分`)
    }
    parts.push('')
  }
  const detail = r.full_report || r.comparison?.detailed_report || ''
  if (detail) {
    parts.push('## 详细报告')
    parts.push(detail)
  }
  const blob = new Blob([parts.join('\n')], { type: 'text/markdown;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `report_${r.product_id}_${r.created_at?.slice(0,10) || 'unknown'}.md`
  a.click()
  URL.revokeObjectURL(a.href)
}

onMounted(async () => {
  try { products.value = await getProducts() } catch { /* ignore */ }
  await load()
})
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>历史报告</h1>
        <p style="color:var(--text-secondary);margin-top:4px;font-size:14px;">浏览与检索历次分析结果</p>
      </div>
      <div style="display:flex;gap:8px;align-items:center;">
        <select
          v-model="filterProductId"
          @change="load"
          style="padding:8px 14px;border:1.5px solid var(--border);border-radius:8px;font-size:13px;font-family:inherit;background:var(--bg);outline:none;"
        >
          <option value="">全部产品</option>
          <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <button class="btn btn-ghost btn-sm" @click="load">刷新</button>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!reports.length" class="empty"><p>暂无历史报告</p></div>

    <div v-else class="card">
      <div class="card-body">
        <table style="table-layout:fixed;">
          <colgroup>
            <col style="width:18%;">
            <col style="width:18%;">
            <col style="width:9%;">
            <col style="width:22%;">
            <col style="width:22%;">
            <col style="width:11%;">
          </colgroup>
          <thead>
            <tr>
              <th>产品</th>
              <th>时间</th>
              <th>状态</th>
              <th>优势</th>
              <th>短板</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in reports" :key="r.id">
              <td style="font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">产品 #{{ r.product_id }}</td>
              <td style="color:var(--text-muted);font-size:12px;white-space:nowrap;">{{ r.created_at?.replace('T', ' ') }}</td>
              <td>
                <span class="pill" :class="r.comparison?.conclusion ? 'pill-green' : 'pill-blue'" style="white-space:nowrap;">
                  {{ r.comparison?.conclusion ? '已评分' : '已生成' }}
                </span>
              </td>
              <td>
                <span v-if="r.comparison?.strengths?.length" style="font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:block;">
                  {{ r.comparison.strengths.map(s => s.维度 || s.dimension).filter(Boolean).join('、') }}
                </span>
                <span v-else style="color:var(--text-muted);font-size:12px;">—</span>
              </td>
              <td>
                <span v-if="r.comparison?.weaknesses?.length" style="font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:block;">
                  {{ r.comparison.weaknesses.map(w => w.维度 || w.dimension).filter(Boolean).join('、') }}
                </span>
                <span v-else style="color:var(--text-muted);font-size:12px;">—</span>
              </td>
              <td style="white-space:nowrap;">
                <button class="btn btn-ghost btn-sm" @click="openReport(r)">查看</button>
                <button
                  v-if="confirmId !== r.id"
                  class="btn btn-sm"
                  style="color:var(--red);background:transparent;margin-left:4px;"
                  @click="confirmId = r.id"
                >删除</button>
                <template v-else>
                  <button class="btn btn-sm" style="color:#fff;background:var(--red);margin-left:4px;" @click="doDelete(r.id)">确认</button>
                  <button class="btn btn-ghost btn-sm" style="margin-left:2px;" @click="confirmId = null">取消</button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 查看报告弹窗 -->
    <div v-if="viewReport" class="modal-overlay" @click.self="viewReport = null">
      <div class="modal" style="width:680px;max-height:85vh;overflow:hidden;display:flex;flex-direction:column;">
        <div style="flex-shrink:0;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
            <h3 style="margin:0;">产品 #{{ viewReport.product_id }} 分析报告</h3>
            <div style="display:flex;gap:6px;">
              <button class="btn btn-ghost btn-sm" @click="exportMd">导出 MD</button>
              <button class="btn btn-ghost btn-sm" @click="viewReport = null">关闭</button>
            </div>
          </div>
          <div style="color:var(--text-muted);font-size:12px;margin-bottom:12px;">{{ viewReport.created_at }}</div>

          <div v-if="viewReport.comparison?.conclusion" style="margin-bottom:12px;padding:12px 16px;background:var(--accent-light);border-radius:8px;font-size:14px;line-height:1.6;">
            <strong>结论：</strong>{{ viewReport.comparison.conclusion }}
          </div>

          <div v-if="viewReport.comparison?.dimension_scores" style="margin-bottom:12px;">
            <div style="font-size:13px;font-weight:600;margin-bottom:6px;">维度评分</div>
            <div v-for="(val, key) in viewReport.comparison.dimension_scores" :key="key" style="display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid var(--border);">
              <span style="width:130px;font-size:13px;font-weight:500;text-align:left;flex-shrink:0;">{{ key }}</span>
              <span style="flex:1;height:6px;background:var(--bg);border-radius:3px;overflow:hidden;">
                <span :style="{ display:'block',height:'100%',borderRadius:'3px',width:val+'%',background:val>=60?'var(--green)':'var(--red)' }"></span>
              </span>
              <span :style="{ width:'36px',fontSize:'13px',fontWeight:700,color:val>=60?'var(--green)':'var(--red)' }">{{ val }}</span>
            </div>
          </div>
        </div>

        <div style="flex:1;min-height:0;overflow-y:auto;">
          <div style="font-size:13px;font-weight:600;margin-bottom:6px;">详细报告</div>
          <pre style="white-space:pre-wrap;font-family:inherit;font-size:13px;line-height:1.7;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:14px;margin:0;">{{ viewReport.full_report || viewReport.comparison?.detailed_report || '无详情' }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>
