import { defineStore } from 'pinia'
import { getDashboardSummary } from '../api/dashboard'

export const useAppStore = defineStore('app', {
  state: () => ({
    collapsed: false,
    projectName: '中文情感分析可视化系统',
    activeModel: null,
    overview: {
      total_count: 0,
      positive_count: 0,
      negative_count: 0,
      average_confidence: 0,
      low_confidence_count: 0,
    },
    lastUpdatedAt: '',
  }),
  getters: {
    activeModelName(state) {
      return state.activeModel?.model_name || '暂无激活模型'
    },
  },
  actions: {
    toggleSidebar() {
      this.collapsed = !this.collapsed
    },
    applySummary(summary) {
      this.projectName = summary.project_name || this.projectName
      this.activeModel = summary.active_model || null
      this.overview = summary.overview || this.overview
      this.lastUpdatedAt = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    },
    async fetchSummary() {
      const summary = await getDashboardSummary()
      this.applySummary(summary)
      return summary
    },
  },
})
