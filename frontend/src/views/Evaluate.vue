<script setup>
import {
  CircleCheck,
  Connection,
  Histogram,
  PieChart,
  Refresh,
} from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { getLatestEvaluation } from '../api/evaluate'
import { getTrainLog } from '../api/train'
import ChartCard from '../components/ChartCard.vue'
import PageHeader from '../components/PageHeader.vue'
import StatCard from '../components/StatCard.vue'
import { formatDecimal, formatPercent } from '../utils/format'

const loading = ref(false)
const evaluation = ref({
  accuracy: null,
  precision_score: null,
  recall_score: null,
  f1_score: null,
  train_loss: null,
  val_loss: null,
  train_losses: [],
  val_losses: [],
  confusion_matrix: [],
  confusion_matrix_url: null,
  loss_curve_url: null,
  model_name: null,
  dataset_name: null,
  epoch_count: null,
  batch_size: null,
  learning_rate: null,
  max_length: null,
  created_at: null,
  finished_at: null,
  classification_report: [],
  model_info: {},
})

function parseLossSeriesFromLog(content) {
  const text = String(content || '')
  const pattern = /epoch=(\d+),\s*train_loss=([0-9.]+),\s*val_loss=([0-9.]+)/g
  const rows = []
  let matched = pattern.exec(text)

  while (matched) {
    rows.push({
      epoch: Number(matched[1]),
      trainLoss: Number(matched[2]),
      valLoss: Number(matched[3]),
    })
    matched = pattern.exec(text)
  }

  rows.sort((left, right) => left.epoch - right.epoch)

  return {
    train_losses: rows.map((item) => Number(item.trainLoss.toFixed(6))),
    val_losses: rows.map((item) => Number(item.valLoss.toFixed(6))),
  }
}

async function loadTrainLogContent(taskId) {
  try {
    const logData = await getTrainLog(taskId)
    if (logData?.content) {
      return logData.content
    }
  } catch {
    // Ignore API failure and continue to static log fallback.
  }

  const candidatePaths = [
    `/storage/logs/train_task_${taskId}.log`,
    `/storage/logs/train_task_${taskId}_manual.log`,
  ]

  for (const path of candidatePaths) {
    try {
      const response = await fetch(path)
      if (!response.ok) {
        continue
      }
      const text = await response.text()
      if (text.trim()) {
        return text
      }
    } catch {
      // Continue to the next candidate path.
    }
  }

  return ''
}

async function loadEvaluation() {
  loading.value = true
  try {
    const data = await getLatestEvaluation()

    const trainSeries = data.train_losses || []
    const valSeries = data.val_losses || []
    const needsLogFallback = (trainSeries.length <= 1 || valSeries.length <= 1) && data.latest_task?.id

    if (needsLogFallback) {
      try {
        const logContent = await loadTrainLogContent(data.latest_task.id)
        const parsedSeries = parseLossSeriesFromLog(logContent)
        if (parsedSeries.train_losses.length > 1 && parsedSeries.val_losses.length > 1) {
          data.train_losses = parsedSeries.train_losses
          data.val_losses = parsedSeries.val_losses
          data.loss_series = parsedSeries
          data.loss_series_source = 'train_log_fallback'
        }
      } catch {
        // Keep the original payload when log fallback is unavailable.
      }
    }

    evaluation.value = data
  } finally {
    loading.value = false
  }
}

function displayPercent(value) {
  return value == null ? '--' : formatPercent(value, 2)
}

function buildFallbackReport(matrix, accuracy, precisionScore, recallScore, f1Score) {
  if (!Array.isArray(matrix) || matrix.length !== 2 || matrix.some((row) => !Array.isArray(row) || row.length !== 2)) {
    return []
  }

  const negativeTrue = Number(matrix[0][0] || 0)
  const negativeFalse = Number(matrix[0][1] || 0)
  const positiveFalse = Number(matrix[1][0] || 0)
  const positiveTrue = Number(matrix[1][1] || 0)
  const safeDiv = (numerator, denominator) => (denominator ? numerator / denominator : 0)
  const safeF1 = (precision, recall) => (precision + recall ? (2 * precision * recall) / (precision + recall) : 0)

  const negativePrecision = safeDiv(negativeTrue, negativeTrue + positiveFalse)
  const negativeRecall = safeDiv(negativeTrue, negativeTrue + negativeFalse)
  const positivePrecision = safeDiv(positiveTrue, negativeFalse + positiveTrue)
  const positiveRecall = safeDiv(positiveTrue, positiveFalse + positiveTrue)

  return [
    {
      label: '消极',
      precision: negativePrecision,
      recall: negativeRecall,
      f1_score: safeF1(negativePrecision, negativeRecall),
      support: negativeTrue + negativeFalse,
    },
    {
      label: '积极',
      precision: positivePrecision,
      recall: positiveRecall,
      f1_score: safeF1(positivePrecision, positiveRecall),
      support: positiveFalse + positiveTrue,
    },
    {
      label: '整体',
      precision: precisionScore || 0,
      recall: recallScore || 0,
      f1_score: f1Score || 0,
      support: negativeTrue + negativeFalse + positiveFalse + positiveTrue,
      accuracy: accuracy || 0,
    },
  ]
}

const classificationReport = computed(() => {
  if ((evaluation.value.classification_report || []).length) {
    return evaluation.value.classification_report
  }
  return buildFallbackReport(
    evaluation.value.confusion_matrix || [],
    evaluation.value.accuracy,
    evaluation.value.precision_score,
    evaluation.value.recall_score,
    evaluation.value.f1_score
  )
})

const epochLabels = computed(() => {
  const count = Math.max(
    evaluation.value.train_losses?.length || 0,
    evaluation.value.val_losses?.length || 0
  )
  return Array.from({ length: count }, (_, index) => `Epoch ${index + 1}`)
})

const hasLossSeries = computed(() => epochLabels.value.length > 1)
const hasConfusionMatrix = computed(() => (evaluation.value.confusion_matrix || []).length > 0)
const showLossImageFallback = computed(() => !hasLossSeries.value && Boolean(evaluation.value.loss_curve_url))
const showMatrixImageFallback = computed(() => !hasConfusionMatrix.value && Boolean(evaluation.value.confusion_matrix_url))

const lossOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { top: 0, textStyle: { color: '#475569' } },
  grid: { left: 24, right: 24, top: 48, bottom: 24, containLabel: true },
  xAxis: {
    type: 'category',
    data: epochLabels.value,
    axisLine: { lineStyle: { color: '#cbd5e1' } },
    axisLabel: { color: '#64748b' },
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: '#64748b' },
    splitLine: { lineStyle: { color: '#e2e8f0' } },
  },
  series: [
    {
      name: '训练 Loss',
      type: 'line',
      smooth: true,
      data: evaluation.value.train_losses || [],
      itemStyle: { color: '#2f6bff' },
      lineStyle: { color: '#2f6bff', width: 3 },
      areaStyle: { color: 'rgba(47,107,255,0.12)' },
    },
    {
      name: '验证 Loss',
      type: 'line',
      smooth: true,
      data: evaluation.value.val_losses || [],
      itemStyle: { color: '#ef4444' },
      lineStyle: { color: '#ef4444', width: 3 },
    },
  ],
}))

const confusionOption = computed(() => ({
  tooltip: {
    formatter(params) {
      const labels = ['消极', '积极']
      return `真实标签：${labels[params.data[1]]}<br/>预测标签：${labels[params.data[0]]}<br/>样本数：${params.data[2]}`
    },
  },
  grid: { left: 24, right: 24, top: 24, bottom: 36, containLabel: true },
  xAxis: {
    type: 'category',
    data: ['消极', '积极'],
    axisLine: { lineStyle: { color: '#cbd5e1' } },
    axisLabel: { color: '#475569' },
  },
  yAxis: {
    type: 'category',
    data: ['消极', '积极'],
    axisLine: { lineStyle: { color: '#cbd5e1' } },
    axisLabel: { color: '#475569' },
  },
  visualMap: {
    min: 0,
    max: Math.max(
      ...((evaluation.value.confusion_matrix || []).flat().map((item) => Number(item || 0))),
      0
    ),
    calculable: false,
    orient: 'horizontal',
    left: 'center',
    bottom: 0,
    inRange: {
      color: ['#e0ecff', '#2f6bff'],
    },
  },
  series: [
    {
      type: 'heatmap',
      label: {
        show: true,
        color: '#0f172a',
        fontWeight: 700,
      },
      data: (evaluation.value.confusion_matrix || []).flatMap((row, rowIndex) =>
        row.map((value, columnIndex) => [columnIndex, rowIndex, Number(value || 0)])
      ),
    },
  ],
}))

onMounted(loadEvaluation)
</script>

<template>
  <div class="page-grid">
    <PageHeader
      title="模型评估增强展示"
      description="集中展示最新已完成训练任务的 Accuracy、Precision、Recall、F1、Loss 曲线、混淆矩阵、分类报告和训练参数信息。"
      tag="Evaluation Report"
    >
      <el-button type="primary" plain :icon="Refresh" @click="loadEvaluation">刷新评估结果</el-button>
    </PageHeader>

    <div class="stat-grid">
      <StatCard title="Accuracy" :value="displayPercent(evaluation.accuracy)" subtitle="整体预测准确率" :icon="CircleCheck" accent="#2f6bff" />
      <StatCard title="Precision" :value="displayPercent(evaluation.precision_score)" subtitle="预测精度指标" :icon="PieChart" accent="#16a34a" />
      <StatCard title="Recall" :value="displayPercent(evaluation.recall_score)" subtitle="正类召回能力" :icon="Connection" accent="#f59e0b" />
      <StatCard title="F1-score" :value="displayPercent(evaluation.f1_score)" subtitle="综合平衡指标" :icon="Histogram" accent="#6366f1" />
    </div>

    <div class="three-col-grid">
      <div class="card-panel metric-note">
        <span>训练 Loss</span>
        <strong>{{ formatDecimal(evaluation.train_loss, 4) }}</strong>
      </div>
      <div class="card-panel metric-note">
        <span>验证 Loss</span>
        <strong>{{ formatDecimal(evaluation.val_loss, 4) }}</strong>
      </div>
      <div class="card-panel metric-note">
        <span>评估模型</span>
        <strong>{{ evaluation.model_name || '暂无完成训练任务' }}</strong>
      </div>
    </div>

    <div class="chart-grid">
      <ChartCard
        title="训练 / 验证 Loss 曲线"
        description="优先使用 metrics.json 中的训练损失序列；若旧任务缺失序列，则显示已有曲线图片。"
        :option="hasLossSeries ? lossOption : null"
        :loading="loading"
        :empty="!hasLossSeries && !showLossImageFallback"
      >
        <el-image v-if="showLossImageFallback" :src="evaluation.loss_curve_url" fit="contain" class="image-view">
          <template #error>
            <div class="image-empty">Loss 曲线图片不存在</div>
          </template>
        </el-image>
      </ChartCard>

      <ChartCard
        title="混淆矩阵"
        description="横轴表示预测标签，纵轴表示真实标签，可直观看到积极 / 消极样本的识别偏差。"
        :option="hasConfusionMatrix ? confusionOption : null"
        :loading="loading"
        :empty="!hasConfusionMatrix && !showMatrixImageFallback"
      >
        <el-image v-if="showMatrixImageFallback" :src="evaluation.confusion_matrix_url" fit="contain" class="image-view">
          <template #error>
            <div class="image-empty">混淆矩阵图片不存在</div>
          </template>
        </el-image>
      </ChartCard>
    </div>

    <div class="two-col-grid">
      <div class="card-panel table-card">
        <div class="table-card__header">
          <div>
            <h3>分类报告表</h3>
            <p>至少展示消极、积极和整体三行指标，适合答辩时说明模型对两类情感的识别效果。</p>
          </div>
        </div>
        <el-table :data="classificationReport" stripe empty-text="暂无分类报告数据">
          <el-table-column prop="label" label="类别" width="120" />
          <el-table-column label="Precision" min-width="120">
            <template #default="{ row }">{{ formatPercent(row.precision, 2) }}</template>
          </el-table-column>
          <el-table-column label="Recall" min-width="120">
            <template #default="{ row }">{{ formatPercent(row.recall, 2) }}</template>
          </el-table-column>
          <el-table-column label="F1-score" min-width="120">
            <template #default="{ row }">{{ formatPercent(row.f1_score, 2) }}</template>
          </el-table-column>
          <el-table-column prop="support" label="Support" min-width="100" />
          <el-table-column label="Accuracy" min-width="120">
            <template #default="{ row }">
              {{ row.accuracy == null ? '--' : formatPercent(row.accuracy, 2) }}
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="page-grid info-grid">
        <div class="card-panel info-card">
          <div class="info-card__title">模型基本信息</div>
          <div class="info-card__item">
            <span>模型名称</span>
            <strong>{{ evaluation.model_name || '--' }}</strong>
          </div>
          <div class="info-card__item">
            <span>数据集</span>
            <strong>{{ evaluation.dataset_name || '--' }}</strong>
          </div>
          <div class="info-card__item">
            <span>模型目录</span>
            <strong>{{ evaluation.model_info?.model_dir || '--' }}</strong>
          </div>
          <div class="info-card__item">
            <span>训练完成时间</span>
            <strong>{{ evaluation.finished_at || '--' }}</strong>
          </div>
        </div>

        <div class="card-panel info-card">
          <div class="info-card__title">训练参数信息</div>
          <div class="info-card__item">
            <span>epoch</span>
            <strong>{{ evaluation.epoch_count ?? '--' }}</strong>
          </div>
          <div class="info-card__item">
            <span>batch_size</span>
            <strong>{{ evaluation.batch_size ?? '--' }}</strong>
          </div>
          <div class="info-card__item">
            <span>learning_rate</span>
            <strong>{{ evaluation.learning_rate ?? '--' }}</strong>
          </div>
          <div class="info-card__item">
            <span>max_length</span>
            <strong>{{ evaluation.max_length ?? '--' }}</strong>
          </div>
          <div class="info-card__item">
            <span>创建时间</span>
            <strong>{{ evaluation.created_at || '--' }}</strong>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.metric-note {
  padding: 22px;
}

.metric-note span {
  display: block;
  color: var(--text-secondary);
  font-size: 13px;
}

.metric-note strong {
  display: block;
  margin-top: 10px;
  color: var(--text-primary);
  font-size: 24px;
  line-height: 1.5;
}

.info-grid {
  gap: 18px;
}

.info-card {
  padding: 22px;
}

.info-card__title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.info-card__item {
  padding: 16px 0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.14);
}

.info-card__item:last-child {
  border-bottom: 0;
}

.info-card__item span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
}

.info-card__item strong {
  display: block;
  margin-top: 8px;
  color: var(--text-primary);
  line-height: 1.7;
  word-break: break-all;
}

.image-view {
  width: 100%;
  height: 100%;
}

.image-empty {
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}
</style>
