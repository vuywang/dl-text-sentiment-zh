import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layout/MainLayout.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: {
          title: '首页看板',
          description: '查看系统整体运行状态、分析统计、趋势图表与近期任务概览。',
        },
      },
      {
        path: 'predict',
        name: 'predict',
        component: () => import('../views/Predict.vue'),
        meta: {
          title: '单文本分析',
          description: '输入中文文本，快速查看积极或消极判断、置信度与概率分布。',
        },
      },
      {
        path: 'batch',
        name: 'batch',
        component: () => import('../views/BatchAnalysis.vue'),
        meta: {
          title: '批量情感分析',
          description: '上传带有 text 列的 CSV 文件，生成统计报告、图表与结果导出。',
        },
      },
      {
        path: 'train',
        name: 'train',
        component: () => import('../views/Train.vue'),
        meta: {
          title: '模型训练',
          description: '设置训练参数、启动训练任务并查看近期训练状态与日志。',
        },
      },
      {
        path: 'evaluate',
        name: 'evaluate',
        component: () => import('../views/Evaluate.vue'),
        meta: {
          title: '模型评估',
          description: '查看 Accuracy、Precision、Recall、F1、Loss 曲线、混淆矩阵和分类报告。',
        },
      },
      {
        path: 'review',
        name: 'review',
        component: () => import('../views/Review.vue'),
        meta: {
          title: '低置信度复核',
          description: '筛选 confidence < 0.60 的记录，展示建议人工复核的预测结果。',
        },
      },
      {
        path: 'error-analysis',
        name: 'error-analysis',
        component: () => import('../views/ErrorAnalysis.vue'),
        meta: {
          title: '误判分析',
          description: '聚焦疑似难判样本与可能原因，辅助展示中文情感分析中的难点场景。',
        },
      },
      {
        path: 'models',
        name: 'models',
        component: () => import('../views/ModelManage.vue'),
        meta: {
          title: '模型管理',
          description: '查看模型注册信息、切换当前启用模型，并对比主要评估指标。',
        },
      },
      {
        path: 'history',
        name: 'history',
        component: () => import('../views/History.vue'),
        meta: {
          title: '历史记录',
          description: '按单文本、批量任务、训练任务三个维度查看系统历史记录。',
        },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
