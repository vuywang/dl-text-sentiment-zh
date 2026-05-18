<script setup>
import { Download, FolderOpened, UploadFilled } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getBatchDetail, getBatchDownloadUrl, uploadBatchFile } from '../api/batch'
import { getBatchHistory } from '../api/history'
import ChartCard from '../components/ChartCard.vue'
import PageHeader from '../components/PageHeader.vue'
import SentimentBadge from '../components/SentimentBadge.vue'
import StatCard from '../components/StatCard.vue'
import { buildTopWords, formatPercent, truncateText } from '../utils/format'

const loading = ref(false)
const selectedFile = ref(null)
const fileList = ref([])
const recentTasks = ref([])
const batchData = ref(null)

function handleFileChange(file, files) {
  selectedFile.value = file.raw
  fileList.value = files.slice(-1)
}

function clearFile() {
  selectedFile.value = null
  fileList.value = []
}

async function loadRecentTasks() {
  recentTasks.value = (await getBatchHistory()).slice(0, 8)
}

async function handleUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择包含 text 列的 CSV 文件')
    return
  }
  loading.value = true
  try {
    batchData.value = await uploadBatchFile(selectedFile.value)
    clearFile()
    await loadRecentTasks()
  } finally {
    loading.value = false
  }
}

async function loadTask(taskId) {
  loading.value = true
  try {
    batchData.value = await getBatchDetail(taskId)
  } finally {
    loading.value = false
  }
}

function downloadResult() {
  if (!batchData.value?.task?.id) {
    return
  }
  window.open(getBatchDownloadUrl(batchData.value.task.id), '_blank')
}

const report = computed(() => batchData.value?.report || {
  total_count: 0,
  positive_count: 0,
  negative_count: 0,
  positive_ratio: 0,
  negative_ratio: 0,
  average_confidence: 0,
  low_confidence_count: 0,
})

const sentimentOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [
    {
      type: 'pie',
      radius: ['45%', '72%'],
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 4,
      },
      color: ['#16a34a', '#ef4444'],
      label: { formatter: '{b}\n{d}%' },
      data: batchData.value?.chart || [],
    },
  ],
}))

const confidenceOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 18, right: 18, top: 24, bottom: 24, containLabel: true },
  xAxis: {
    type: 'category',
    data: (batchData.value?.confidence_distribution || []).map((item) => item.range),
    axisLabel: { color: '#64748b' },
    axisLine: { lineStyle: { color: '#cbd5e1' } },
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: '#64748b' },
    splitLine: { lineStyle: { color: '#e2e8f0' } },
  },
  series: [
    {
      type: 'bar',
      barWidth: 28,
      itemStyle: {
        borderRadius: [10, 10, 0, 0],
      },
      data: (batchData.value?.confidence_distribution || []).map((item, index) => ({
        value: item.count,
        itemStyle: {
          color: ['#ef4444', '#f97316', '#f59e0b', '#22c55e', '#2f6bff'][index],
        },
      })),
    },
  ],
}))

const lengthOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 18, right: 18, top: 24, bottom: 24, containLabel: true },
  xAxis: {
    type: 'category',
    data: (batchData.value?.length_distribution || []).map((item) => item.range),
    axisLabel: { color: '#64748b' },
    axisLine: { lineStyle: { color: '#cbd5e1' } },
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: '#64748b' },
    splitLine: { lineStyle: { color: '#e2e8f0' } },
  },
  series: [
    {
      type: 'bar',
      barWidth: 28,
      itemStyle: {
        borderRadius: [10, 10, 0, 0],
        color: '#2f6bff',
      },
      data: (batchData.value?.length_distribution || []).map((item) => item.count),
    },
  ],
}))

const topWords = computed(() => {
  if (batchData.value?.top_words?.length) {
    return batchData.value.top_words
  }
  return buildTopWords(batchData.value?.preview || [])
})

const topWordsOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 18, right: 18, top: 24, bottom: 24, containLabel: true },
  xAxis: {
    type: 'value',
    axisLabel: { color: '#64748b' },
    splitLine: { lineStyle: { color: '#e2e8f0' } },
  },
  yAxis: {
    type: 'category',
    data: topWords.value.map((item) => item.word),
    axisLabel: { color: '#64748b' },
  },
  series: [
    {
      type: 'bar',
      data: topWords.value.map((item) => item.count),
      barWidth: 18,
      itemStyle: {
        borderRadius: 12,
        color: '#6366f1',
      },
    },
  ],
}))

onMounted(loadRecentTasks)
</script>

<template>
  <div class="page-grid">
    <PageHeader
      title="批量情感分析"
      description="上传包含 text 列的 CSV 文件，生成情感分布、置信度分布、文本长度分布和高频词统计等展示型报告。"
      tag="Batch Report"
    >
      <el-button type="primary" plain :icon="FolderOpened" @click="loadRecentTasks">刷新任务列表</el-button>
    </PageHeader>

    <div class="two-col-grid">
      <div class="card-panel upload-panel">
        <div class="upload-panel__head">
          <div>
            <h3>CSV 文件上传</h3>
            <p>上传要求：必须包含 <code>text</code> 列，编码支持 UTF-8 / UTF-8-SIG。</p>
          </div>
          <el-tag type="primary" round>支持答辩演示数据快速导入</el-tag>
        </div>

        <el-upload
          drag
          action="#"
          :auto-upload="false"
          :on-change="handleFileChange"
          :file-list="fileList"
          :limit="1"
          accept=".csv"
          class="upload-panel__drag"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">将 CSV 文件拖到此处，或<em>点击选择文件</em></div>
          <template #tip>
            <div class="el-upload__tip">推荐使用仓库中的 <code>storage/datasets/sample_batch.csv</code> 进行演示。</div>
          </template>
        </el-upload>

        <div class="upload-panel__actions">
          <el-button type="primary" size="large" :loading="loading" @click="handleUpload">上传并分析</el-button>
          <el-button size="large" @click="clearFile">清空文件</el-button>
          <el-button
            v-if="batchData?.task?.id"
            type="success"
            size="large"
            :icon="Download"
            @click="downloadResult"
          >
            下载结果
          </el-button>
        </div>
      </div>

      <div class="card-panel table-card">
        <div class="table-card__header">
          <div>
            <h3>最近批量任务</h3>
            <p>点击“查看报告”可直接切换到历史任务详情。</p>
          </div>
        </div>
        <el-table :data="recentTasks" stripe max-height="360">
          <el-table-column prop="original_file_name" label="文件名" min-width="220" />
          <el-table-column prop="total_count" label="总量" width="90" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button text type="primary" @click="loadTask(row.id)">查看报告</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <div v-if="batchData" class="page-grid">
      <div class="stat-grid">
        <StatCard title="总文本数" :value="report.total_count" subtitle="本次任务参与分析的文本总量" accent="#2f6bff" />
        <StatCard title="积极数量" :value="report.positive_count" subtitle="预测为积极情感的文本数量" accent="#16a34a" />
        <StatCard title="消极数量" :value="report.negative_count" subtitle="预测为消极情感的文本数量" accent="#ef4444" />
        <StatCard title="平均置信度" :value="formatPercent(report.average_confidence, 2)" subtitle="整体预测把握程度" accent="#6366f1" />
      </div>

      <div class="three-col-grid">
        <StatCard title="积极占比" :value="formatPercent(report.positive_ratio, 2)" subtitle="积极文本比例" accent="#16a34a" />
        <StatCard title="消极占比" :value="formatPercent(report.negative_ratio, 2)" subtitle="消极文本比例" accent="#ef4444" />
        <StatCard title="低置信度数量" :value="report.low_confidence_count" subtitle="建议人工复核的文本数" accent="#f97316" />
      </div>

      <div class="chart-grid">
        <ChartCard
          title="情感占比饼图"
          description="从整体上观察本次批量任务中积极与消极文本的结构。"
          :option="sentimentOption"
          :loading="loading"
          :empty="!(batchData.chart || []).length"
        />
        <ChartCard
          title="置信度分布柱状图"
          description="重点展示低置信度与高置信度文本的分层情况。"
          :option="confidenceOption"
          :loading="loading"
          :empty="!(batchData.confidence_distribution || []).length"
        />
      </div>

      <div class="chart-grid">
        <ChartCard
          title="文本长度分布"
          description="查看短文本与长文本的占比，辅助说明不同文本长度下的建模难点。"
          :option="lengthOption"
          :loading="loading"
          :empty="!(batchData.length_distribution || []).length"
        />
        <ChartCard
          title="高频词 Top 10"
          description="根据批量结果中的文本内容提取高频短词，用于展示主题与情感线索。"
          :option="topWordsOption"
          :loading="loading"
          :empty="!topWords.length"
        />
      </div>

      <div class="card-panel table-card">
        <div class="table-card__header">
          <div>
            <h3>批量预测结果预览</h3>
            <p>默认展示前 {{ batchData.preview_limit || 200 }} 条记录，含情感标签与概率字段。</p>
          </div>
        </div>
        <el-table :data="batchData.preview" stripe max-height="420">
          <el-table-column label="文本内容" min-width="360">
            <template #default="{ row }">
              <el-tooltip :content="row.text" placement="top-start">
                <span>{{ truncateText(row.text, 42) }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column label="情感" width="100">
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
        </el-table>
      </div>

      <div class="chart-grid">
        <div class="card-panel table-card">
          <div class="table-card__header">
            <div>
              <h3>低置信度文本列表</h3>
              <p>建议在答辩时说明这类文本更适合结合人工复核。</p>
            </div>
          </div>
          <el-table :data="batchData.low_confidence_preview" stripe max-height="320">
            <el-table-column label="文本内容" min-width="260">
              <template #default="{ row }">
                <el-tooltip :content="row.text" placement="top-start">
                  <span>{{ truncateText(row.text, 30) }}</span>
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
          </el-table>
        </div>

        <div class="card-panel table-card">
          <div class="table-card__header">
            <div>
              <h3>高置信度消极文本</h3>
              <p>常用于展示系统对明显负面评价的识别能力。</p>
            </div>
          </div>
          <el-table :data="batchData.high_confidence_negative_preview" stripe max-height="320">
            <el-table-column label="文本内容" min-width="260">
              <template #default="{ row }">
                <el-tooltip :content="row.text" placement="top-start">
                  <span>{{ truncateText(row.text, 30) }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="消极概率" width="110">
              <template #default="{ row }">{{ formatPercent(row.negative_score, 2) }}</template>
            </el-table-column>
            <el-table-column label="置信度" width="110">
              <template #default="{ row }">{{ formatPercent(row.confidence, 2) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.upload-panel {
  padding: 22px;
}

.upload-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.upload-panel__head h3 {
  margin: 0;
  font-size: 18px;
}

.upload-panel__head p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
  font-size: 13px;
}

.upload-panel__drag :deep(.el-upload-dragger) {
  width: 100%;
  border-radius: 22px;
  border: 1px dashed rgba(47, 107, 255, 0.35);
  background: linear-gradient(180deg, rgba(47, 107, 255, 0.04), rgba(255, 255, 255, 0.98));
}

.upload-panel__actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 22px;
}
</style>
