<script setup>
import { ref } from 'vue'

const message = ref('')
const analyzing = ref(false)
const result = ref(null)
const thoughts = ref([])
const error = ref('')

const stepNames = ['理解意图', '产品匹配', '情感分析', '聚合对比', '短板深挖', '生成报告']
const currentStep = ref(-1)

async function run() {
  if (!message.value.trim()) return
  analyzing.value = true
  error.value = ''
  result.value = null
  thoughts.value = []
  currentStep.value = 0

  try {
    const res = await fetch('/api/analyze/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: message.value }),
    })

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
        if (line.startsWith('data: ')) {
          const evt = JSON.parse(line.slice(6))
          if (evt.event === 'thought') {
            thoughts.value.push(evt.data)
            currentStep.value = Math.min(currentStep.value + 1, 5)
          } else if (evt.event === 'result') {
            result.value = evt.data
            currentStep.value = 6
          }
        }
      }
    }
  } catch (e) {
    error.value = e.message
  } finally {
    analyzing.value = false
    currentStep.value = 6
  }
}

function scoreColor(score) {
  if (score >= 80) return 'var(--green)'
  if (score >= 60) return '#D4A853'
  return 'var(--red)'
}

function scoreBarBg(score) {
  if (score >= 80) return 'linear-gradient(90deg,#7C9A7E,#9DB89F)'
  if (score >= 60) return 'linear-gradient(90deg,#D4A853,#E8C49A)'
  return 'linear-gradient(90deg,#C47A6B,#D49589)'
}
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>竞品分析</h1>
        <p style="color:var(--text-secondary);margin-top:6px;font-size:15px;">AI 驱动六步分析 · 流式实时展示</p>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="card">
      <div class="card-pad">
        <div class="form-group" style="margin-bottom:0;">
          <label>分析需求</label>
          <div style="display:flex;gap:12px;">
            <input
              v-model="message"
              placeholder="输入分析需求，例如：帮我分析一下小米手环9 Pro的竞品情况"
              style="flex:1;"
              @keyup.enter="run"
            />
            <button class="btn btn-primary" :disabled="analyzing" @click="run" style="padding:10px 28px;">
              {{ analyzing ? '分析中...' : '开始分析 →' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <!-- 分析过程 -->
    <div v-if="thoughts.length || analyzing" class="card" style="margin-top:20px;">
      <div class="card-header">
        <h3>分析过程</h3>
        <span class="pill" :class="analyzing ? 'pill-accent' : 'pill-green'">
          {{ analyzing ? '运行中' : '已完成' }}
        </span>
      </div>
      <div class="card-pad">
        <div
          v-for="(step, i) in stepNames"
          :key="i"
          class="flow-step"
          :style="{ opacity: i < currentStep || (i === currentStep && !analyzing) ? 1 : i === currentStep ? 1 : 0.5 }"
        >
          <div
            class="step-dot"
            :class="i < currentStep ? 'done' : i === currentStep && analyzing ? 'active' : 'wait'"
          >
            {{ i < currentStep ? '✓' : i + 1 }}
          </div>
          <div class="step-body">
            <h4 :style="{ color: i > currentStep ? 'var(--text-muted)' : 'inherit' }">{{ step }}</h4>
            <p v-if="thoughts[i]">{{ thoughts[i].detail || thoughts[i].status }}</p>
            <p v-else-if="i === currentStep && analyzing" style="color:var(--accent);">处理中...</p>
            <p v-else-if="i > currentStep">等待前置步骤...</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 结果 -->
    <div v-if="result" class="card" style="margin-top:20px;">
      <div class="card-header">
        <h3>对比报告</h3>
      </div>
      <div class="card-pad">
        <!-- 维度评分 -->
        <div v-if="result.comparison?.dimension_scores">
          <h4 style="font-size:16px;font-weight:600;margin-bottom:20px;">维度评分对比</h4>
          <div
            v-for="(score, dim) in result.comparison.dimension_scores"
            :key="dim"
            class="score-row"
          >
            <div class="dim">{{ dim }}</div>
            <div class="track">
              <div class="fill" :style="{ width: score + '%', background: scoreBarBg(score) }"></div>
            </div>
            <div class="val" :style="{ color: scoreColor(score) }">{{ score }}</div>
          </div>
        </div>

        <!-- 短板 -->
        <div v-if="result.weaknesses?.length" style="margin-top:20px;">
          <h4 style="font-size:15px;font-weight:600;margin-bottom:12px;">短板维度</h4>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <span
              v-for="w in result.weaknesses"
              :key="w.维度"
              class="tag tag-red"
              style="padding:6px 14px;font-size:12px;"
            >
              {{ w.维度 }}：本品 {{ w.本品评分 }} vs 竞品 {{ w.竞品平均 }}（差距 {{ w.差距 }}）
            </span>
          </div>
        </div>

        <!-- 深挖 -->
        <div
          v-if="result.deep_dive"
          style="margin-top:20px;padding:20px;background:var(--red-light);border-radius:var(--radius-lg);font-size:14px;line-height:1.8;white-space:pre-wrap;"
        >
          {{ typeof result.deep_dive === 'string' ? result.deep_dive : JSON.stringify(result.deep_dive, null, 2) }}
        </div>

        <!-- 完整报告 -->
        <div
          v-if="result.full_report"
          style="margin-top:20px;font-size:14px;line-height:1.8;white-space:pre-wrap;"
        >
          {{ result.full_report }}
        </div>
      </div>
    </div>
  </div>
</template>
