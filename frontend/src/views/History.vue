<script setup>
import { computed, onMounted, ref } from 'vue'
import { getBatchDownloadUrl } from '../api/batch'
import { getAnalysisHistory, getBatchHistory, getTrainHistory } from '../api/history'
import { getTrainLog } from '../api/train'
import PageHeader from '../components/PageHeader.vue'
import SentimentBadge from '../components/SentimentBadge.vue'
import { formatPercent, truncateText } from '../utils/format'

const activeTab = ref('analysis')
const keyword = ref('')
const loading = ref(false)
const historyData = ref({
  analysis: [],
  batch: [],
  train: [],
})
const logVisible = ref(false)
const logContent = ref('')
const logTitle = ref('')
const logLoading = ref(false)

async function loadData() {
  loading.value = true
  try {
    const [analysis, batch, train] = await Promise.all([
      getAnalysisHistory(),
      getBatchHistory(),
      getTrainHistory(),
    ])
    historyData.value = { analysis, batch, train }
  } finally {
    loading.value = false
  }
}

const filteredAnalysis = computed(() =>
  historyData.value.analysis.filter((item) => item.input_text.includes(keyword.value))
)

const filteredBatch = computed(() =>
  historyData.value.batch.filter((item) => item.original_file_name.includes(keyword.value))
)

const filteredTrain = computed(() =>
  historyData.value.train.filter((item) => item.model_name.includes(keyword.value))
)

async function openLog(task) {
  logVisible.value = true
  logLoading.value = true
  logTitle.value = task.model_name
  try {
    const response = await getTrainLog(task.id)
    logContent.value = response.content || '当前暂无日志输出。'
  } finally {
    logLoading.value = false
  }
}

function downloadBatch(taskId) {
  window.open(getBatchDownloadUrl(taskId), '_blank')
}

onMounted(loadData)
</script>

<template>
  <div class="page-grid">
    <PageHeader
      title="历史记录中心"
      description="使用 Tabs 分栏展示单文本分析历史、批量任务历史和训练任务历史，便于答辩时说明系统具有数据持久化能力。"
      tag="History Center"
    >
      <el-input v-model="keyword" clearable placeholder="输入关键词筛选当前页数据" style="width: 280px" />
    </PageHeader>

    <div class="card-panel table-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="单文本分析历史" name="analysis">
          <el-table v-loading="loading" :data="filteredAnalysis" stripe>
            <el-table-column label="文本内容" min-width="360">
              <template #default="{ row }">
                <el-tooltip :content="row.input_text" placement="top-start">
                  <span>{{ truncateText(row.input_text, 42) }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="情感" width="100">
              <template #default="{ row }">
                <SentimentBadge :label="row.predicted_label" />
              </template>
            </el-table-column>
            <el-table-column label="置信度" width="110">
              <template #default="{ row }">{{ formatPercent(row.confidence, 2) }}</template>
            </el-table-column>
            <el-table-column prop="model_name" label="模型名称" min-width="220" />
            <el-table-column prop="created_at" label="创建时间" min-width="160" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="批量分析任务历史" name="batch">
          <el-table v-loading="loading" :data="filteredBatch" stripe>
            <el-table-column prop="original_file_name" label="文件名" min-width="220" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="total_count" label="总量" width="90" />
            <el-table-column label="积极 / 消极" min-width="130">
              <template #default="{ row }">{{ row.positive_count }} / {{ row.negative_count }}</template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" min-width="160" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button text type="primary" @click="downloadBatch(row.id)">下载结果</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="训练任务历史" name="train">
          <el-table v-loading="loading" :data="filteredTrain" stripe>
            <el-table-column prop="model_name" label="模型名称" min-width="240" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="epoch_count" label="epoch" width="90" />
            <el-table-column prop="batch_size" label="batch_size" width="110" />
            <el-table-column prop="accuracy" label="Accuracy" width="110" />
            <el-table-column prop="created_at" label="创建时间" min-width="160" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button text type="primary" @click="openLog(row)">训练日志</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog v-model="logVisible" width="900px" :title="`训练日志：${logTitle}`">
      <el-skeleton v-if="logLoading" animated :rows="8" />
      <pre v-else class="log-content">{{ logContent }}</pre>
    </el-dialog>
  </div>
</template>

<style scoped>
.log-content {
  margin: 0;
  max-height: 520px;
  overflow: auto;
  padding: 18px;
  border-radius: 18px;
  background: #0f172a;
  color: #dbeafe;
  font-family: Consolas, "Courier New", monospace;
  line-height: 1.7;
  white-space: pre-wrap;
}
</style>
