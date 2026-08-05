const BASE = '/api'

async function request(url, options = {}) {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ---- 产品 CRUD ----
export const getProducts = () => request('/products')
export const getProduct = (id) => request(`/products/${id}`)
export const createProduct = (data) => request('/products', { method: 'POST', body: JSON.stringify(data) })
export const updateProduct = (id, data) => request(`/products/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteProduct = (id) => request(`/products/${id}`, { method: 'DELETE' })

// ---- 评价 CRUD ----
export const getReviews = (productId) => {
  const qs = productId ? `?product_id=${productId}` : ''
  return request(`/reviews${qs}`)
}
export const createReview = (data) => request('/reviews', { method: 'POST', body: JSON.stringify(data) })
export const updateReview = (id, data) => request(`/reviews/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteReview = (id) => request(`/reviews/${id}`, { method: 'DELETE' })

// ---- 评价标签 CRUD ----
export const getReviewTags = (reviewId) => request(`/review-tags?review_id=${reviewId}`)
export const createReviewTag = (data) => request('/review-tags', { method: 'POST', body: JSON.stringify(data) })
export const updateReviewTag = (id, data) => request(`/review-tags/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteReviewTag = (id) => request(`/review-tags/${id}`, { method: 'DELETE' })

// ---- 竞品分析 ----
export const analyze = (message) => request('/analyze', { method: 'POST', body: JSON.stringify({ message }) })

// ---- 历史报告 ----
export const getReports = (productId, page = 1, pageSize = 20) => {
  const qs = new URLSearchParams({ page, page_size: pageSize })
  if (productId) qs.set('product_id', productId)
  return request(`/reports?${qs}`)
}
export const getReport = (id) => request(`/reports/${id}`)
export const deleteReport = (id) => request(`/reports/${id}`, { method: 'DELETE' })

// ---- RAG 知识库 ----
export const getRagStatus = () => request('/rag/status')

// ---- 健康检查 ----
export const healthCheck = () => request('/health')
