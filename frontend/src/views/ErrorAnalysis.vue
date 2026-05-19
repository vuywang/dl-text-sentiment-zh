<script setup>
import { onMounted, ref } from 'vue'
import { getErrorSamples } from '../api/evaluate'
import PageHeader from '../components/PageHeader.vue'
import SentimentBadge from '../components/SentimentBadge.vue'
import StatCard from '../components/StatCard.vue'
import { formatPercent, truncateText } from '../utils/format'

const loading = ref(false)
const errorData = ref({
  items: [],
  summary: {
    scan_count: 0,
    error_count: 0,
    message: '',
  },
})

async function loadData() {
  loading.value = true
  try {
    errorData.value = await getErrorSamples({
      limit: 30,
      scan_limit: 300,
    })
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="page-grid">
    <PageHeader
      title="误判样本分析页面"
      description="基于历史分析记录中的低置信度和疑似难判样本，展示中文情感分析在否定、转折、短文本和复杂表达上的挑战。"
      tag="Error Analysis"
    />

    <el-alert
      title="中文情感分析中，否定、转折、反讽、短文本和情感混合表达容易影响模型判断，因此系统对低置信度和疑似难判样本进行展示分析。"
      type="info"
      :closable="false"
    />

    <div class="three-col-grid">
      <StatCard title="扫描记录数" :value="errorData.summary.scan_count" subtitle="本次从历史记录中扫描的候选样本数" accent="#2f6bff" />
      <StatCard title="疑似难判样本数" :value="errorData.summary.error_count" subtitle="用于答辩展示的重点分析样本" accent="#f97316" />
      <StatCard title="分析说明" :value="errorData.items.length ? '已生成' : '空状态'" subtitle="无数据时不伪造样本，直接展示空状态" accent="#6366f1" />
    </div>

    <div class="card-panel table-card">
      <div class="table-card__header">
        <div>
          <h3>疑似误判 / 难判样本列表</h3>
          <p>{{ errorData.summary.message || '如果当前没有数据，页面会显示空状态。' }}</p>
        </div>
      </div>

      <el-table v-loading="loading" :data="errorData.items" stripe empty-text="当前没有可展示的疑似误判样本">
        <el-table-column label="文本内容" min-width="360">
          <template #default="{ row }">
            <el-tooltip :content="row.input_text" placement="top-start">
              <span>{{ truncateText(row.input_text, 48) }}</span>
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
        <el-table-column prop="possible_reason" label="可能原因" min-width="180" />
        <el-table-column prop="created_at" label="创建时间" min-width="160" />
      </el-table>
    </div>
  </div>
</template>
