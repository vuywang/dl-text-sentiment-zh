<script setup>
import {
  CircleCheck,
  Connection,
  Histogram,
  PieChart,
} from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { getLatestEvaluation } from '../api/evaluate'
import ChartCard from '../components/ChartCard.vue'
import PageHeader from '../components/PageHeader.vue'
import SentimentBadge from '../components/SentimentBadge.vue'
import StatCard from '../components/StatCard.vue'
import { formatDecimal, formatPercent, toChartArray, truncateText } from '../utils/format'

const loading = ref(false)
const evaluation = ref({
  latest_task: null,
  metric_cards: null,
  confusion_matrix: [],
  confusion_matrix_url: null,
  loss_curve_url: null,
  loss_series: {
    train_losses: [],
    val_losses: [],
  },
  sample_predictions: [],
  model_comparison: [],
})

async function loadEvaluation() {
  loading.value = true
  try {
    evaluation.value = await getLatestEvaluation()
  } finally {
    loading.value = false
  }
}

const metricCards = computed(() => evaluation.value.metric_cards || {})

const confusionOption = computed(() => ({
  tooltip: {
    formatter(params) {
      const labels = ['消极', '积极']
      return `真实：${labels[params.data[1]]}<br/>预测：${labels[params.data[0]]}<br/>数量：${params.data[2]}`
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
    max: Math.max(...toChartArray(evaluation.value.confusion_matrix).map((item) => item[2]), 0),
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
      data: toChartArray(evaluation.value.confusion_matrix),
    },
  ],
}))

const lossOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { top: 0 },
  grid: { left: 24, right: 24, top: 48, bottom: 24, containLabel: true },
  xAxis: {
    type: 'category',
    data: evaluation.value.loss_series.train_losses.map((_, index) => `Epoch ${index + 1}`),
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
      name: '训练损失',
      type: 'line',
      smooth: true,
      data: evaluation.value.loss_series.train_losses,
      itemStyle: { color: '#2f6bff' },
      lineStyle: { color: '#2f6bff', width: 3 },
      areaStyle: { color: 'rgba(47,107,255,0.12)' },
    },
    {
      name: '验证损失',
      type: 'line',
      smooth: true,
      data: evaluation.value.loss_series.val_losses,
      itemStyle: { color: '#ef4444' },
      lineStyle: { color: '#ef4444', width: 3 },
    },
  ],
}))

const hasLossSeries = computed(() => evaluation.value.loss_series.train_losses.length > 0)
const hasConfusionMatrix = computed(() => (evaluation.value.confusion_matrix || []).length > 0)
const showMatrixImageFallback = computed(
  () => !hasConfusionMatrix.value && Boolean(evaluation.value.confusion_matrix_url)
)
const showLossImageFallback = computed(
  () => !hasLossSeries.value && Boolean(evaluation.value.loss_curve_url)
)

onMounted(loadEvaluation)
</script>

<template>
  <div class="page-grid">
    <PageHeader
      title="模型评估可视化"
      description="集中展示最新训练任务的核心指标、混淆矩阵、损失曲线、测试样例预测以及多模型对比结果。"
      tag="Evaluation Report"
    >
      <div class="eval-extra">
        <div class="eval-extra__item">
          <span>评估模型</span>
          <strong>{{ evaluation.latest_task?.model_name || '暂无完成训练任务' }}</strong>
        </div>
      </div>
    </PageHeader>

    <div class="stat-grid">
      <StatCard title="Accuracy" :value="formatPercent(metricCards.accuracy, 2)" subtitle="整体预测准确率" :icon="CircleCheck" accent="#2f6bff" />
      <StatCard title="Precision" :value="formatPercent(metricCards.precision, 2)" subtitle="积极类预测精度" :icon="PieChart" accent="#16a34a" />
      <StatCard title="Recall" :value="formatPercent(metricCards.recall, 2)" subtitle="积极类召回率" :icon="Connection" accent="#f59e0b" />
      <StatCard title="F1-score" :value="formatPercent(metricCards.f1_score, 2)" subtitle="综合平衡指标" :icon="Histogram" accent="#6366f1" />
    </div>

    <div class="chart-grid">
      <ChartCard
        title="混淆矩阵"
        description="横轴为预测标签，纵轴为真实标签，用于观察正负样本识别偏差。"
        :option="hasConfusionMatrix ? confusionOption : null"
        :loading="loading"
        :empty="!hasConfusionMatrix && !showMatrixImageFallback"
      >
        <el-image v-if="showMatrixImageFallback" :src="evaluation.confusion_matrix_url" fit="contain" class="image-view" />
      </ChartCard>

      <ChartCard
        title="训练 / 验证损失曲线"
        description="优先使用训练产生的损失序列，若旧任务缺少序列数据则展示原始曲线图片。"
        :option="hasLossSeries ? lossOption : null"
        :loading="loading"
        :empty="!hasLossSeries && !showLossImageFallback"
      >
        <el-image v-if="showLossImageFallback" :src="evaluation.loss_curve_url" fit="contain" class="image-view" />
      </ChartCard>
    </div>

    <div class="two-col-grid">
      <div class="card-panel table-card">
        <div class="table-card__header">
          <div>
            <h3>测试样例预测结果</h3>
            <p>用于答辩中快速展示模型对典型中文评论文本的实时推理效果。</p>
          </div>
        </div>
        <el-table :data="evaluation.sample_predictions" stripe>
          <el-table-column label="文本内容" min-width="260">
            <template #default="{ row }">
              <el-tooltip :content="row.text" placement="top-start">
                <span>{{ truncateText(row.text, 32) }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column label="预测情感" width="100">
            <template #default="{ row }">
              <SentimentBadge :label="row.predicted_label" />
            </template>
          </el-table-column>
          <el-table-column label="积极概率" width="110">
            <template #default="{ row }">{{ formatPercent(row.positive_score, 2) }}</template>
          </el-table-column>
          <el-table-column label="置信度" width="100">
            <template #default="{ row }">{{ formatPercent(row.confidence, 2) }}</template>
          </el-table-column>
        </el-table>
      </div>

      <div class="card-panel metric-panel">
        <div class="table-card__header">
          <div>
            <h3>补充指标说明</h3>
            <p>适合在答辩时快速解释训练结果和当前模型配置。</p>
          </div>
        </div>

        <div class="metric-panel__item">
          <span>训练损失</span>
          <strong>{{ formatDecimal(metricCards.train_loss, 4) }}</strong>
        </div>
        <div class="metric-panel__item">
          <span>验证损失</span>
          <strong>{{ formatDecimal(metricCards.val_loss, 4) }}</strong>
        </div>
        <div class="metric-panel__item">
          <span>训练参数</span>
          <strong>
            epoch={{ evaluation.train_config?.epoch ?? '--' }} /
            batch_size={{ evaluation.train_config?.batch_size ?? '--' }} /
            max_length={{ evaluation.train_config?.max_length ?? '--' }}
          </strong>
        </div>
        <div class="metric-panel__item">
          <span>当前样例预测模型</span>
          <strong>{{ evaluation.sample_prediction_model || '--' }}</strong>
        </div>
      </div>
    </div>

    <div class="card-panel table-card">
      <div class="table-card__header">
        <div>
          <h3>模型对比表</h3>
          <p>基于模型注册信息与训练任务指标，展示不同模型的效果差异与启用状态。</p>
        </div>
      </div>
      <el-table :data="evaluation.model_comparison" stripe>
        <el-table-column prop="model_name" label="模型名称" min-width="240" />
        <el-table-column prop="model_type" label="模型类型" width="110" />
        <el-table-column label="Accuracy" width="110">
          <template #default="{ row }">{{ row.accuracy == null ? '--' : formatPercent(row.accuracy, 2) }}</template>
        </el-table-column>
        <el-table-column label="Precision" width="110">
          <template #default="{ row }">{{ row.precision == null ? '--' : formatPercent(row.precision, 2) }}</template>
        </el-table-column>
        <el-table-column label="Recall" width="110">
          <template #default="{ row }">{{ row.recall == null ? '--' : formatPercent(row.recall, 2) }}</template>
        </el-table-column>
        <el-table-column label="F1-score" width="110">
          <template #default="{ row }">{{ row.f1_score == null ? '--' : formatPercent(row.f1_score, 2) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="160" />
        <el-table-column label="是否启用" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '当前启用' : '未启用' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.eval-extra__item {
  padding: 12px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
}

.eval-extra__item span {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
}

.eval-extra__item strong {
  display: block;
  margin-top: 8px;
  color: var(--text-primary);
}

.image-view {
  width: 100%;
  height: 100%;
}

.metric-panel {
  padding: 20px;
}

.metric-panel__item {
  padding: 18px;
  border-radius: 18px;
  background: rgba(245, 247, 251, 0.92);
}

.metric-panel__item + .metric-panel__item {
  margin-top: 12px;
}

.metric-panel__item span {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
}

.metric-panel__item strong {
  display: block;
  margin-top: 10px;
  line-height: 1.7;
  color: var(--text-primary);
}
</style>
