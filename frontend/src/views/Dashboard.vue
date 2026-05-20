<script setup>
import {
  CircleCheckFilled,
  Cpu,
  DataLine,
  Document,
  TrendCharts,
  WarningFilled,
} from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { getDashboardSummary } from '../api/dashboard'
import ChartCard from '../components/ChartCard.vue'
import PageHeader from '../components/PageHeader.vue'
import SentimentBadge from '../components/SentimentBadge.vue'
import StatCard from '../components/StatCard.vue'
import { useAppStore } from '../stores/app'
import { formatPercent, truncateText } from '../utils/format'

const appStore = useAppStore()
const loading = ref(false)
const summary = ref({
  overview: {
    total_count: 0,
    positive_count: 0,
    negative_count: 0,
    average_confidence: 0,
    low_confidence_count: 0,
  },
  active_model: null,
  latest_train_task: null,
  latest_batch_task: null,
  recent_train_tasks: [],
  recent_batch_tasks: [],
  recent_analysis_records: [],
  recent_records: [],
  sentiment_chart: [],
  trend_chart: [],
  model_metric_chart: null,
})

async function loadData() {
  loading.value = true
  try {
    const summaryData = await getDashboardSummary()
    summary.value = summaryData
    appStore.applySummary(summaryData)
  } finally {
    loading.value = false
  }
}

const pieOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: {
    bottom: 0,
    itemWidth: 10,
    textStyle: { color: '#475569' },
  },
  series: [
    {
      type: 'pie',
      radius: ['48%', '72%'],
      center: ['50%', '46%'],
      avoidLabelOverlap: false,
      label: {
        formatter: '{b}\n{d}%',
        color: '#0f172a',
        fontWeight: 600,
      },
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 4,
      },
      color: ['#22c55e', '#ef4444'],
      data: summary.value.sentiment_chart || [],
    },
  ],
}))

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: {
    top: 0,
    textStyle: { color: '#475569' },
  },
  grid: {
    left: 24,
    right: 24,
    bottom: 24,
    top: 48,
    containLabel: true,
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: (summary.value.trend_chart || []).map((item) => item.date),
    axisLine: { lineStyle: { color: '#cbd5e1' } },
    axisLabel: { color: '#64748b' },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#e2e8f0' } },
    axisLabel: { color: '#64748b' },
  },
  series: [
    {
      name: '总量',
      type: 'line',
      smooth: true,
      lineStyle: { width: 3, color: '#2f6bff' },
      itemStyle: { color: '#2f6bff' },
      areaStyle: { color: 'rgba(47,107,255,0.14)' },
      data: (summary.value.trend_chart || []).map((item) => item.total),
    },
    {
      name: '积极',
      type: 'line',
      smooth: true,
      lineStyle: { width: 2, color: '#16a34a' },
      itemStyle: { color: '#16a34a' },
      data: (summary.value.trend_chart || []).map((item) => item.positive),
    },
    {
      name: '消极',
      type: 'line',
      smooth: true,
      lineStyle: { width: 2, color: '#ef4444' },
      itemStyle: { color: '#ef4444' },
      data: (summary.value.trend_chart || []).map((item) => item.negative),
    },
  ],
}))

const metricOption = computed(() => {
  const metrics = summary.value.model_metric_chart
  return {
    tooltip: {},
    radar: {
      indicator: [
        { name: 'Accuracy', max: 1 },
        { name: 'Precision', max: 1 },
        { name: 'Recall', max: 1 },
        { name: 'F1-score', max: 1 },
      ],
      splitLine: { lineStyle: { color: 'rgba(99, 102, 241, 0.12)' } },
      splitArea: { areaStyle: { color: ['rgba(47,107,255,0.02)', 'rgba(47,107,255,0.04)'] } },
      axisName: { color: '#475569' },
    },
    series: [
      {
        type: 'radar',
        areaStyle: { color: 'rgba(47,107,255,0.22)' },
        lineStyle: { color: '#2f6bff', width: 2 },
        itemStyle: { color: '#2f6bff' },
        data: [
          {
            value: metrics
              ? [metrics.accuracy, metrics.precision, metrics.recall, metrics.f1_score]
              : [0, 0, 0, 0],
            name: metrics?.model_name || '暂无数据',
          },
        ],
      },
    ],
  }
})

onMounted(loadData)
</script>

<template>
  <div class="page-grid">
    <PageHeader
      title="中文情感分析可视化看板"
      tag="System Dashboard"
    >
      <div class="header-meta">
        <div class="header-meta__item">
          <span>数据库状态</span>
          <strong>{{ summary.db_status || '已连接' }}</strong>
        </div>
        <div class="header-meta__item">
          <span>当前模型</span>
          <strong>{{ summary.active_model?.model_name || '暂无激活模型' }}</strong>
        </div>
      </div>
    </PageHeader>

    <div class="stat-grid">
      <StatCard
        title="累计分析文本数"
        :value="summary.overview.total_count"
        subtitle="包含单文本与批量分析记录"
        :icon="Document"
        accent="#2f6bff"
      />
      <StatCard
        title="积极文本数量"
        :value="summary.overview.positive_count"
        subtitle="系统已识别为积极的文本条数"
        :icon="CircleCheckFilled"
        accent="#16a34a"
      />
      <StatCard
        title="消极文本数量"
        :value="summary.overview.negative_count"
        subtitle="系统已识别为消极的文本条数"
        :icon="WarningFilled"
        accent="#ef4444"
      />
      <StatCard
        title="平均置信度"
        :value="formatPercent(summary.average_confidence)"
        subtitle="用于衡量整体预测稳定度"
        :icon="DataLine"
        accent="#6366f1"
      />
    </div>

    <div class="two-col-grid">
      <div class="card-panel overview-panel">
        <div class="overview-panel__head">
          <div>
            <h3>系统概览</h3>
            <p>模型、最近训练与最近批量任务一屏展示。</p>
          </div>
          <SentimentBadge
            v-if="summary.latest_batch_task"
            :label="summary.latest_batch_task.positive_count >= summary.latest_batch_task.negative_count ? '积极' : '消极'"
          />
        </div>

        <div class="overview-panel__body">
          <div class="overview-block">
            <div class="overview-block__label">当前使用模型</div>
            <div class="overview-block__value">{{ summary.active_model?.model_name || '暂无模型' }}</div>
            <div class="overview-block__meta">
              类型：{{ summary.active_model?.model_type || '--' }}｜
              备注：{{ summary.active_model?.remark || '无' }}
            </div>
          </div>

          <div class="overview-block">
            <div class="overview-block__label">最近训练任务</div>
            <div class="overview-block__value">{{ summary.latest_train_task?.model_name || '暂无训练任务' }}</div>
            <div class="overview-block__meta">
              状态：{{ summary.latest_train_task?.status || '--' }}｜
              Accuracy：{{ summary.latest_train_task?.accuracy ?? '--' }}
            </div>
          </div>

          <div class="overview-block">
            <div class="overview-block__label">最近批量分析任务</div>
            <div class="overview-block__value">{{ summary.latest_batch_task?.original_file_name || '暂无批量任务' }}</div>
            <div class="overview-block__meta">
              总量：{{ summary.latest_batch_task?.total_count ?? 0 }}｜
              创建时间：{{ summary.latest_batch_task?.created_at || '--' }}
            </div>
          </div>
        </div>
      </div>

      <div class="card-panel overview-panel">
        <div class="overview-panel__head">
          <div>
            <h3>答辩展示提示</h3>
          </div>
          <el-icon class="overview-panel__head-icon"><Cpu /></el-icon>
        </div>

        <div class="overview-tips">
          <div class="overview-tip">
            <strong>{{ summary.overview.low_confidence_count }}</strong>
            <span>条低置信度文本建议人工复核</span>
          </div>
          <div class="overview-tip">
            <strong>{{ summary.model_metric_chart?.model_name || '暂无训练结果' }}</strong>
            <span>用于右侧模型性能雷达图展示</span>
          </div>
          <div class="overview-tip">
            <strong>{{ (summary.recent_records || summary.recent_analysis_records || []).length }}</strong>
            <span>条近期记录可作为实时演示数据入口</span>
          </div>
        </div>
      </div>
    </div>

    <div class="chart-grid">
      <ChartCard
        title="积极 / 消极占比"
        description="基于系统累计分析记录统计整体情感分布。"
        :option="pieOption"
        :loading="loading"
        :empty="!(summary.sentiment_chart || []).length"
      />
      <ChartCard
        title="最近分析趋势"
        description="展示近 7 天文本分析总量及积极、消极变化趋势。"
        :option="trendOption"
        :loading="loading"
        :empty="!(summary.trend_chart || []).length"
      />
    </div>

    <div class="two-col-grid">
      <ChartCard
        title="模型指标雷达图"
        description="选取最新完成训练任务的 Accuracy、Precision、Recall、F1 作为答辩展示重点。"
        :option="metricOption"
        :loading="loading"
        :empty="!summary.model_metric_chart"
      />

      <div class="card-panel table-card">
        <div class="table-card__header">
          <div>
            <h3>最近分析记录</h3>
            <p>可直接观察近期预测文本内容、标签和置信度表现。</p>
          </div>
        </div>
        <el-table :data="summary.recent_records || summary.recent_analysis_records" stripe empty-text="暂无分析记录">
          <el-table-column label="文本内容" min-width="260">
            <template #default="{ row }">
              <el-tooltip :content="row.input_text" placement="top-start">
                <span>{{ truncateText(row.input_text, 30) }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column label="情感" width="100">
            <template #default="{ row }">
              <SentimentBadge :label="row.predicted_label" />
            </template>
          </el-table-column>
          <el-table-column label="置信度" width="110">
            <template #default="{ row }">{{ formatPercent(row.confidence) }}</template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" min-width="160" />
        </el-table>
      </div>
    </div>

    <div class="chart-grid">
      <div class="card-panel table-card">
        <div class="table-card__header">
          <div>
            <h3>最近训练任务</h3>
            <p>保留模型名称、状态、Accuracy 和创建时间，适合答辩时说明训练过程。</p>
          </div>
        </div>
        <el-table :data="summary.recent_train_tasks" stripe empty-text="暂无训练任务记录">
          <el-table-column prop="model_name" label="模型名称" min-width="220" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="accuracy" label="Accuracy" width="110" />
          <el-table-column prop="created_at" label="创建时间" min-width="160" />
        </el-table>
      </div>

      <div class="card-panel table-card">
        <div class="table-card__header">
          <div>
            <h3>最近批量分析任务</h3>
            <p>文件名、任务规模和情感分布能够很好体现系统的批量处理能力。</p>
          </div>
        </div>
        <el-table :data="summary.recent_batch_tasks" stripe empty-text="暂无批量任务记录">
          <el-table-column prop="original_file_name" label="文件名" min-width="220" />
          <el-table-column prop="total_count" label="总量" width="90" />
          <el-table-column label="积极 / 消极" min-width="130">
            <template #default="{ row }">
              {{ row.positive_count }} / {{ row.negative_count }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" min-width="160" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.header-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.header-meta__item {
  padding: 12px 16px;
  min-width: 180px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
}

.header-meta__item span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
}

.header-meta__item strong {
  display: block;
  margin-top: 8px;
  color: var(--text-primary);
}

.overview-panel {
  padding: 22px;
}

.overview-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.overview-panel__head h3 {
  margin: 0;
  font-size: 18px;
}

.overview-panel__head p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.overview-panel__head-icon {
  font-size: 24px;
  color: #2f6bff;
}

.overview-panel__body {
  display: grid;
  gap: 16px;
  margin-top: 20px;
}

.overview-block {
  padding: 18px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(245, 247, 251, 0.9), rgba(255, 255, 255, 0.96));
  border: 1px solid rgba(148, 163, 184, 0.15);
}

.overview-block__label {
  font-size: 13px;
  color: var(--text-secondary);
}

.overview-block__value {
  margin-top: 10px;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.6;
}

.overview-block__meta {
  margin-top: 8px;
  color: var(--text-secondary);
  line-height: 1.7;
  font-size: 13px;
}

.overview-tips {
  display: grid;
  gap: 14px;
  margin-top: 22px;
}

.overview-tip {
  padding: 18px;
  border-radius: 20px;
  background: linear-gradient(90deg, rgba(47, 107, 255, 0.12), rgba(87, 163, 255, 0.04));
}

.overview-tip strong {
  display: block;
  font-size: 22px;
  color: #295df4;
}

.overview-tip span {
  display: block;
  margin-top: 8px;
  color: var(--text-secondary);
}
</style>
