<script setup>
import { onMounted, ref } from 'vue'
import { getErrorSamples } from '../api/evaluate'
import PageHeader from '../components/PageHeader.vue'
import SentimentBadge from '../components/SentimentBadge.vue'
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
      limit: 20,
      scan_limit: 200,
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
      title="误判样本分析"
      description="基于评估数据集扫描得到的误判样本，结合简单规则解释情感转折、否定表达和低置信度等难点现象。"
      tag="Error Analysis"
    />

    <el-alert
      :title="errorData.summary.message || '若当前没有可用误判样本，页面会以空状态展示。'"
      type="info"
      :closable="false"
    />

    <div class="three-col-grid">
      <div class="card-panel error-stat">
        <strong>{{ errorData.summary.scan_count }}</strong>
        <span>扫描评估样本数</span>
      </div>
      <div class="card-panel error-stat">
        <strong>{{ errorData.summary.error_count }}</strong>
        <span>识别到的误判样本数</span>
      </div>
      <div class="card-panel error-stat">
        <strong>规则解释</strong>
        <span>用于展示情感转折、否定表达与语义复杂性。</span>
      </div>
    </div>

    <div class="card-panel table-card">
      <div class="table-card__header">
        <div>
          <h3>误判样本表格</h3>
          <p>可在答辩时挑选 2 到 3 条典型文本，说明中文情感分析的复杂性与模型改进方向。</p>
        </div>
      </div>

      <el-table v-loading="loading" :data="errorData.items" stripe>
        <el-table-column label="文本内容" min-width="360">
          <template #default="{ row }">
            <el-tooltip :content="row.text" placement="top-start">
              <span>{{ truncateText(row.text, 48) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="真实标签" width="100">
          <template #default="{ row }">
            <SentimentBadge :label="row.true_label" />
          </template>
        </el-table-column>
        <el-table-column label="预测标签" width="100">
          <template #default="{ row }">
            <SentimentBadge :label="row.predicted_label" />
          </template>
        </el-table-column>
        <el-table-column label="置信度" width="110">
          <template #default="{ row }">{{ formatPercent(row.confidence, 2) }}</template>
        </el-table-column>
        <el-table-column prop="possible_reason" label="可能原因" min-width="220" />
      </el-table>

      <el-empty v-if="!loading && !errorData.items.length" description="当前没有可展示的误判样本" />
    </div>
  </div>
</template>

<style scoped>
.error-stat {
  padding: 24px;
}

.error-stat strong {
  display: block;
  font-size: 28px;
  color: #2f6bff;
}

.error-stat span {
  display: block;
  margin-top: 10px;
  color: var(--text-secondary);
  line-height: 1.7;
}
</style>
