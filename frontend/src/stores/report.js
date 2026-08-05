import { reactive } from 'vue'

export const reportStore = reactive({
  productName: '',
  comparisonReport: '',
  weaknesses: [],
  deepDive: '',
  clear() {
    this.productName = ''
    this.comparisonReport = ''
    this.weaknesses = []
    this.deepDive = ''
  },
  set(data) {
    this.productName = data.product_name || ''
    this.comparisonReport = data.comparison_report || ''
    this.weaknesses = data.weaknesses || []
    this.deepDive = data.deep_dive || ''
  },
})
