<script setup>
import { ref, onMounted } from 'vue'
import {
  getProducts, createProduct, updateProduct, deleteProduct,
  getReviews, createReview, updateReview, deleteReview,
  getReviewTags, createReviewTag, deleteReviewTag,
} from '../api'

const products = ref([])
const reviewsMap = ref({})
const tagsMap = ref({})
const loading = ref(false)
const error = ref('')
const showProductModal = ref(false)
const editProduct = ref(null)
const productForm = ref({ name: '', brand: '', price: 0, category: '', launch_date: '' })
const showReviewModal = ref(false)
const editReview = ref(null)
const reviewForm = ref({ product_id: 0, user_name: '', rating: 5, content: '', sentiment: 'positive' })
const expandedProductId = ref(null)
const newTag = ref({})

async function loadProducts() {
  loading.value = true
  try { products.value = await getProducts() } catch (e) { error.value = e.message }
  loading.value = false
}

function toggleReviews(productId) {
  if (expandedProductId.value === productId) {
    expandedProductId.value = null
  } else {
    expandedProductId.value = productId
    loadReviews(productId)
  }
}

async function loadReviews(productId) {
  reviewsMap.value[productId] = await getReviews(productId)
}

async function loadTags(reviewId) {
  try { tagsMap.value[reviewId] = await getReviewTags(reviewId) } catch { tagsMap.value[reviewId] = [] }
}

function openCreateProduct() {
  editProduct.value = null
  productForm.value = { name: '', brand: '', price: null, category: '', launch_date: null }
  showProductModal.value = true
}

function openEditProduct(p) {
  editProduct.value = p
  productForm.value = { ...p, launch_date: p.launch_date || null }
  showProductModal.value = true
}

async function saveProduct() {
  try {
    const data = { ...productForm.value }
    if (data.launch_date === null || data.launch_date === '') data.launch_date = null
    if (data.price === null || data.price === '') data.price = null
    if (editProduct.value) {
      await updateProduct(editProduct.value.id, data)
    } else {
      await createProduct(data)
    }
    showProductModal.value = false
    await loadProducts()
  } catch (e) { error.value = e.message }
}

async function removeProduct(id) {
  if (!confirm('删除产品会同时删除其下所有评价和标签，确认？')) return
  try { await deleteProduct(id); await loadProducts() } catch (e) { error.value = e.message }
}

function openCreateReview(productId) {
  editReview.value = null
  reviewForm.value = { product_id: productId, user_name: '', rating: 5, content: '', sentiment: 'positive' }
  showReviewModal.value = true
}

function openEditReview(r) {
  editReview.value = r
  reviewForm.value = { ...r }
  showReviewModal.value = true
}

async function saveReview() {
  try {
    if (editReview.value) {
      await updateReview(editReview.value.id, reviewForm.value)
    } else {
      await createReview(reviewForm.value)
    }
    showReviewModal.value = false
    await loadReviews(reviewForm.value.product_id)
  } catch (e) { error.value = e.message }
}

async function removeReview(id, productId) {
  if (!confirm('确认删除？')) return
  try { await deleteReview(id); await loadReviews(productId) } catch (e) { error.value = e.message }
}

async function addTag(reviewId, productId) {
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

function sentimentClass(s) {
  if (s === 'positive') return 'pill-green'
  if (s === 'negative') return 'pill-red'
  return 'pill-blue'
}

function sentimentLabel(s) {
  if (s === 'positive') return '正面'
  if (s === 'negative') return '负面'
  return '中性'
}

onMounted(loadProducts)
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>产品管理</h1>
        <p style="color:var(--text-secondary);margin-top:6px;font-size:15px;">管理产品目录与用户评价</p>
      </div>
      <button class="btn btn-primary" @click="openCreateProduct">+ 添加产品</button>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <div v-if="!loading" class="card">
      <table>
        <thead>
          <tr><th>产品</th><th>品类</th><th>品牌</th><th>价格</th><th>评价</th><th>操作</th></tr>
        </thead>
        <tbody>
          <template v-for="p in products" :key="p.id">
            <tr>
              <td>
                <a
                  href="javascript:void(0)"
                  @click="toggleReviews(p.id)"
                  style="font-weight:600;color:var(--text);text-decoration:none;"
                >
                  {{ expandedProductId === p.id ? '▾' : '▸' }} {{ p.name }}
                </a>
              </td>
              <td><span class="pill pill-accent">{{ p.category }}</span></td>
              <td>{{ p.brand }}</td>
              <td>¥{{ p.price }}</td>
              <td>{{ p.launch_date }}</td>
              <td>
                <button class="btn btn-ghost btn-sm" @click="toggleReviews(p.id)">
                  {{ expandedProductId === p.id ? '收起' : '展开' }}
                </button>
                <button class="btn btn-ghost btn-sm" @click="openEditProduct(p)">编辑</button>
                <button class="btn btn-danger btn-sm" @click="removeProduct(p.id)">删除</button>
              </td>
            </tr>

            <tr v-if="expandedProductId === p.id">
              <td colspan="6" class="expand-row">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
                  <strong style="font-size:14px;font-weight:600;">{{ p.name }} 的用户评价</strong>
                  <button class="btn btn-primary btn-sm" @click="openCreateReview(p.id)">+ 添加评价</button>
                </div>

                <div v-if="!reviewsMap[p.id] || reviewsMap[p.id].length === 0" style="color:var(--text-muted);padding:12px 0;text-align:center;">
                  暂无评价，点击上方按钮添加
                </div>

                <div v-else v-for="r in reviewsMap[p.id]" :key="r.id" class="sub-table" style="margin-bottom:8px;">
                  <table style="margin-bottom:0;">
                    <tbody>
                      <tr>
                        <td style="font-weight:600;">{{ r.user_name || '匿名用户' }}</td>
                        <td><span class="stars">{{ '★'.repeat(r.rating) }}{{ '☆'.repeat(5 - r.rating) }}</span></td>
                        <td><span class="pill" :class="sentimentClass(r.sentiment)">{{ sentimentLabel(r.sentiment) }}</span></td>
                        <td style="text-align:right;">
                          <button class="btn btn-ghost btn-sm" @click="openEditReview(r)">编辑</button>
                          <button class="btn btn-danger btn-sm" @click="removeReview(r.id, p.id)">删除</button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <p style="padding:0 16px 12px;font-size:13px;color:var(--text-secondary);">{{ r.content }}</p>

                  <!-- 标签 -->
                  <div style="padding:0 16px 12px;">
                    <div v-if="tagsMap[r.id]" style="display:flex;flex-wrap:wrap;gap:4px;align-items:center;">
                      <span v-for="t in tagsMap[r.id]" :key="t.id" class="tag tag-green">
                        {{ t.tag_name }}
                        <span v-if="t.dimension" style="color:var(--text-muted);">[{{ t.dimension }}]</span>
                        <button @click="removeTag(t.id, r.id)" style="border:none;background:none;cursor:pointer;color:var(--red);font-weight:700;">&times;</button>
                      </span>
                      <input
                        v-model="newTag[r.id]"
                        placeholder="+ 标签"
                        style="width:70px;padding:2px 6px;font-size:11px;border:1px solid var(--border);border-radius:4px;"
                        @keyup.enter="addTag(r.id, p.id)"
                      />
                    </div>
                    <button v-else class="btn btn-ghost btn-sm" @click="loadTags(r.id)">展开标签</button>
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
    <div v-else class="loading">加载中...</div>

    <!-- 产品弹窗 -->
    <div v-if="showProductModal" class="modal-overlay" @click.self="showProductModal = false">
      <div class="modal">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
          <h3 style="margin:0;">{{ editProduct ? '编辑产品' : '新增产品' }}</h3>
          <button class="btn btn-ghost btn-sm" @click="showProductModal = false">✕</button>
        </div>
        <div class="form-group"><label>产品名称</label><input v-model="productForm.name" placeholder="例：小米手环 9 Pro" /></div>
        <div class="form-group"><label>品类</label><input v-model="productForm.category" placeholder="例：运动手环" /></div>
        <div class="form-group"><label>品牌</label><input v-model="productForm.brand" placeholder="例：小米" /></div>
        <div class="form-group"><label>价格 (¥)</label><input v-model.number="productForm.price" type="number" step="0.01" placeholder="399" /></div>
        <div class="form-group"><label>上市日期</label><input v-model="productForm.launch_date" type="date" /></div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showProductModal = false">取消</button>
          <button class="btn btn-primary" @click="saveProduct">保存产品</button>
        </div>
      </div>
    </div>

    <!-- 评价弹窗 -->
    <div v-if="showReviewModal" class="modal-overlay" @click.self="showReviewModal = false">
      <div class="modal">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
          <h3 style="margin:0;">{{ editReview ? '编辑评价' : '新增评价' }}</h3>
          <button class="btn btn-ghost btn-sm" @click="showReviewModal = false">✕</button>
        </div>
        <div class="form-group"><label>用户昵称</label><input v-model="reviewForm.user_name" placeholder="例：运动达人" /></div>
        <div class="form-group">
          <label>评分</label>
          <select v-model.number="reviewForm.rating">
            <option v-for="n in 5" :key="n" :value="n">{{ '★'.repeat(n) }}{{ '☆'.repeat(5 - n) }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>情感倾向</label>
          <select v-model="reviewForm.sentiment">
            <option value="positive">正面</option>
            <option value="neutral">中性</option>
            <option value="negative">负面</option>
          </select>
        </div>
        <div class="form-group"><label>评价内容</label><textarea v-model="reviewForm.content" placeholder="写下用户评价..."></textarea></div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showReviewModal = false">取消</button>
          <button class="btn btn-primary" @click="saveReview">保存评价</button>
        </div>
      </div>
    </div>
  </div>
</template>
