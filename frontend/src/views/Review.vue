<script setup>
import { computed, onMounted, ref } from 'vue'
import { getLowConfidenceRecords } from '../api/history'
import PageHeader from '../components/PageHeader.vue'
import SentimentBadge from '../components/SentimentBadge.vue'
import StatCard from '../components/StatCard.vue'
import { formatPercent, truncateText } from '../utils/format'

const loading = ref(false)
const filterType = ref('all')
const reviewData = ref({
  items: [],
  summary: {
    total_count: 0,
    positive_count: 0,
    negative_count: 0,
  },
})

async function loadData() {
  loading.value = true
  try {
    reviewData.value = await getLowConfidenceRecords({ limit: 300 })
  } finally {
    loading.value = false
  }
}

const filteredRows = computed(() => {
  if (filterType.value === 'all') {
    return reviewData.value.items
  }
  if (filterType.value === 'review') {
    return reviewData.value.items.filter((item) => item.status === '建议复核')
  }
  return reviewData.value.items.filter((item) => item.predicted_label === filterType.value)
})

onMounted(loadData)
</script>

<template>
  <div class="page-grid">
    <PageHeader
      title="低置信度复核管理"
      description="从历史分析记录中筛选低置信度文本，展示哪些样本更适合进入人工复核流程。"
      tag="Review Queue"
    >
      <el-radio-group v-model="filterType">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="review">建议复核</el-radio-button>
        <el-radio-button label="积极">积极</el-radio-button>
        <el-radio-button label="消极">消极</el-radio-button>
      </el-radio-group>
    </PageHeader>

    <div class="three-col-grid">
      <StatCard title="待复核总数" :value="reviewData.summary.total_count" subtitle="当前低置信度文本总量" accent="#f97316" />
      <StatCard title="积极文本" :value="reviewData.summary.positive_count" subtitle="低置信度中的积极预测样本" accent="#16a34a" />
      <StatCard title="消极文本" :value="reviewData.summary.negative_count" subtitle="低置信度中的消极预测样本" accent="#ef4444" />
    </div>

    <div class="card-panel table-card">
      <div class="table-card__header">
        <div>
          <h3>低置信度文本列表</h3>
          <p>用于展示系统在情感边界较模糊的样本上，会主动提示“建议人工复核”。</p>
        </div>
      </div>
      <el-table v-loading="loading" :data="filteredRows" stripe>
        <el-table-column label="文本内容" min-width="360">
          <template #default="{ row }">
            <el-tooltip :content="row.input_text" placement="top-start">
              <span>{{ truncateText(row.input_text, 42) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="预测标签" width="100">
          <template #default="{ row }">
            <SentimentBadge :label="row.predicted_label" />
          </template>
        </el-table-column>
        <el-table-column label="积极概率" width="110">
          <template #default="{ row }">{{ formatPercent(row.positive_score, 2) }}</template>
        </el-table-column>
        <el-table-column label="消极概率" width="110">
          <template #default="{ row }">{{ formatPercent(row.negative_score, 2) }}</template>
        </el-table-column>
        <el-table-column label="置信度" width="110">
          <template #default="{ row }">{{ formatPercent(row.confidence, 2) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="130">
          <template #default="{ row }">
            <el-tag type="warning" round>{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="160" />
      </el-table>
    </div>
  </div>
</template>
