<script setup>
import { ref, onMounted } from 'vue'
import { getProducts, getReviews, createReview, updateReview, deleteReview, getReviewTags, createReviewTag, deleteReviewTag } from '../api'

const products = ref([])
const reviews = ref([])
const tagsMap = ref({})
const loading = ref(false)
const error = ref('')
const showModal = ref(false)
const editItem = ref(null)
const form = ref({ product_id: 1, user_name: '', rating: 5, content: '', sentiment: 'positive' })
const newTag = ref({})

async function loadProducts() {
  products.value = await getProducts()
}

async function loadReviews() {
  loading.value = true
  try { reviews.value = await getReviews() } catch (e) { error.value = e.message }
  loading.value = false
}

async function loadTags(reviewId) {
  try { tagsMap.value[reviewId] = await getReviewTags(reviewId) } catch { tagsMap.value[reviewId] = [] }
}

function openCreate() {
  editItem.value = null
  form.value = { product_id: products.value[0]?.id || 1, user_name: '', rating: 5, content: '', sentiment: 'positive' }
  showModal.value = true
}

function openEdit(r) {
  editItem.value = r
  form.value = { ...r }
  showModal.value = true
}

async function save() {
  try {
    if (editItem.value) {
      await updateReview(editItem.value.id, form.value)
    } else {
      await createReview(form.value)
    }
    showModal.value = false
    await loadReviews()
  } catch (e) { error.value = e.message }
}

async function remove(id) {
  if (!confirm('确认删除？')) return
  try { await deleteReview(id); await loadReviews() } catch (e) { error.value = e.message }
}

async function addTag(reviewId) {
  const tag = newTag.value[reviewId]
  if (!tag) return
  try {
    await createReviewTag({ review_id: reviewId, tag_name: tag, sentiment: 'neutral', dimension: '' })
    newTag.value[reviewId] = ''
    await loadTags(reviewId)
  } catch (e) { error.value = e.message }
}

async function removeTag(tagId, reviewId) {
  try { await deleteReviewTag(tagId); await loadTags(reviewId) } catch (e) { error.value = e.message }
}

onMounted(async () => {
  await loadProducts()
  await loadReviews()
})
</script>

<template>
  <div>
    <div class="page-header">
      <h1>评价管理</h1>
      <button class="btn btn-primary" @click="openCreate">+ 新增评价</button>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <div v-if="!loading" v-for="r in reviews" :key="r.id" class="card">
      <div style="display:flex;justify-content:space-between;align-items:start;">
        <div>
          <strong>{{ r.user_name }}</strong>
          <span style="margin-left:12px;color:#f39c12;">{{ '★'.repeat(r.rating) }}{{ '☆'.repeat(5 - r.rating) }}</span>
          <span style="margin-left:8px;color:#999;">{{ r.sentiment }}</span>
          <span style="margin-left:12px;color:#bbb;font-size:12px;">{{ r.created_at }}</span>
        </div>
        <div>
          <button class="btn btn-sm btn-default" @click="openEdit(r)">编辑</button>
          <button class="btn btn-sm btn-danger" @click="remove(r.id)">删除</button>
        </div>
      </div>
      <p style="margin-top:8px;">{{ r.content }}</p>

      <!-- 标签 -->
      <div style="margin-top:8px;">
        <button v-if="!tagsMap[r.id]" class="btn btn-sm btn-default" @click="loadTags(r.id)">展开标签</button>
        <div v-else>
          <span v-for="t in tagsMap[r.id]" :key="t.id" style="display:inline-block;background:#f0f0f0;padding:2px 8px;border-radius:4px;margin:2px;font-size:12px;">
            {{ t.tag_name }}
            <span v-if="t.dimension" style="color:#999;">[{{ t.dimension }}]</span>
            <button @click="removeTag(t.id, r.id)" style="border:none;background:none;cursor:pointer;color:#c62828;">&times;</button>
          </span>
          <input
            v-model="newTag[r.id]"
            placeholder="新标签"
            style="width:80px;padding:2px 6px;font-size:12px;margin-left:4px;"
            @keyup.enter="addTag(r.id)"
          />
        </div>
      </div>
    </div>
    <div v-else class="loading">加载中...</div>

    <!-- 编辑弹窗 -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>{{ editItem ? '编辑评价' : '新增评价' }}</h3>
        <div class="form-group">
          <label>产品</label>
          <select v-model.number="form.product_id">
            <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>用户名</label><input v-model="form.user_name" />
        </div>
        <div class="form-group">
          <label>评分</label>
          <select v-model.number="form.rating">
            <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>情感</label>
          <select v-model="form.sentiment">
            <option value="positive">正面</option>
            <option value="neutral">中性</option>
            <option value="negative">负面</option>
          </select>
        </div>
        <div class="form-group">
          <label>内容</label><textarea v-model="form.content"></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn btn-default" @click="showModal = false">取消</button>
          <button class="btn btn-primary" @click="save">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
