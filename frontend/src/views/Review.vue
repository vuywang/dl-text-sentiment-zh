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
    average_confidence: 0,
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
    return reviewData.value.items.filter((item) => item.review_status === '建议复核')
  }
  return reviewData.value.items.filter((item) => item.predicted_label === filterType.value)
})

onMounted(loadData)
</script>

<template>
  <div class="page-grid">
    <PageHeader
      title="低置信度复核页面"
      description="筛选 confidence < 0.60 的分析记录，帮助展示系统如何识别不稳定预测并提示人工复核。"
      tag="Low Confidence Review"
    >
      <el-radio-group v-model="filterType">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="review">建议复核</el-radio-button>
        <el-radio-button label="积极">积极</el-radio-button>
        <el-radio-button label="消极">消极</el-radio-button>
      </el-radio-group>
    </PageHeader>

    <div class="stat-grid">
      <StatCard title="待复核总数" :value="reviewData.summary.total_count" subtitle="confidence < 0.60 的文本记录" accent="#f97316" />
      <StatCard title="积极预测数" :value="reviewData.summary.positive_count" subtitle="低置信度中的积极样本" accent="#16a34a" />
      <StatCard title="消极预测数" :value="reviewData.summary.negative_count" subtitle="低置信度中的消极样本" accent="#ef4444" />
      <StatCard title="平均置信度" :value="formatPercent(reviewData.summary.average_confidence, 2)" subtitle="越低代表越值得人工复核" accent="#2f6bff" />
    </div>

    <div class="card-panel table-card">
      <div class="table-card__header">
        <div>
          <h3>低置信度文本列表</h3>
          <p>页面聚焦“文本内容、预测标签、正负概率、置信度、复核状态、来源类型和创建时间”等答辩重点字段。</p>
        </div>
      </div>
      <el-table v-loading="loading" :data="filteredRows" stripe empty-text="当前没有低置信度记录">
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
        <el-table-column prop="review_status" label="复核状态" width="130">
          <template #default="{ row }">
            <el-tag :type="row.review_status === '建议复核' ? 'warning' : row.review_status === '高可信' ? 'success' : 'info'" round>
              {{ row.review_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source_type" label="来源类型" width="110" />
        <el-table-column prop="created_at" label="创建时间" min-width="160" />
      </el-table>
    </div>
  </div>
</template>
