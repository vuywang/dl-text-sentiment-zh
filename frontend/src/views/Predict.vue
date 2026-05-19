<script setup>
import { Delete, MagicStick } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAnalysisHistory } from '../api/history'
import { predictText } from '../api/predict'
import ChartCard from '../components/ChartCard.vue'
import ConfidenceBar from '../components/ConfidenceBar.vue'
import PageHeader from '../components/PageHeader.vue'
import SentimentBadge from '../components/SentimentBadge.vue'
import { confidenceStatus, formatPercent, truncateText } from '../utils/format'

const inputText = ref('')
const loading = ref(false)
const result = ref(null)
const recentRecords = ref([])

const exampleTexts = [
  { label: '积极样例', text: '这家酒店服务很好，房间干净整洁，下次还会再来。' },
  { label: '消极样例', text: '客服态度不好，问题一直没有解决，整体体验很差。' },
  { label: '复杂样例', text: '包装还可以，但是发货速度有点慢，整体感受一般。' },
]

function fillExample(text) {
  inputText.value = text
}

function clearForm() {
  inputText.value = ''
  result.value = null
}

async function loadRecentRecords() {
  recentRecords.value = (await getAnalysisHistory()).slice(0, 8)
}

async function handlePredict() {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入需要分析的中文文本')
    return
  }
  loading.value = true
  try {
    result.value = await predictText(inputText.value)
    await loadRecentRecords()
  } finally {
    loading.value = false
  }
}

const confidenceMeta = computed(() => confidenceStatus(result.value?.confidence || 0))

const gaugeOption = computed(() => ({
  series: [
    {
      type: 'gauge',
      min: 0,
      max: 100,
      progress: {
        show: true,
        width: 14,
        itemStyle: {
          color: confidenceMeta.value.color,
        },
      },
      axisLine: {
        lineStyle: {
          width: 14,
          color: [[1, '#e2e8f0']],
        },
      },
      splitLine: { show: false },
      axisTick: { show: false },
      axisLabel: { show: false },
      anchor: { show: false },
      detail: {
        formatter: `${((result.value?.confidence || 0) * 100).toFixed(1)}%`,
        color: '#0f172a',
        fontSize: 24,
        fontWeight: 700,
      },
      title: {
        offsetCenter: [0, '72%'],
        color: '#64748b',
      },
      data: [
        {
          value: Number(((result.value?.confidence || 0) * 100).toFixed(1)),
          name: confidenceMeta.value.label,
        },
      ],
    },
  ],
}))

const analysisText = computed(() => {
  if (!result.value) {
    return '输入一段中文文本后，系统会结合 BERT 模型输出情感倾向、概率分布和置信度建议。'
  }
  if (result.value.confidence < 0.6) {
    return '该文本情感表达不够明显，建议结合人工判断进行复核。'
  }
  if (result.value.predicted_label === '积极' && result.value.confidence >= 0.8) {
    return '文本中积极情感特征较明显，系统判断为积极情感。'
  }
  if (result.value.predicted_label === '消极' && result.value.confidence >= 0.8) {
    return '文本中消极情感特征较明显，系统判断为消极情感。'
  }
  return '模型认为该文本具有一定情感倾向，但建议结合上下文进一步判断。'
})

onMounted(loadRecentRecords)
</script>

<template>
  <div class="page-grid">
    <PageHeader
      title="单文本情感分析"
      description="针对输入的中文文本进行即时推理，展示情感标签、正负向概率、置信度等级与解释性说明。"
      tag="Realtime Prediction"
    >
      <div class="example-actions">
        <el-button
          v-for="item in exampleTexts"
          :key="item.label"
          round
          @click="fillExample(item.text)"
        >
          {{ item.label }}
        </el-button>
      </div>
    </PageHeader>

    <div class="two-col-grid predict-grid">
      <div class="card-panel editor-panel">
        <div class="editor-panel__head">
          <div>
            <h3>文本输入区</h3>
            <p>建议输入完整中文句子，便于模型捕捉更清晰的情感表达。</p>
          </div>
        </div>

        <el-input
          v-model="inputText"
          type="textarea"
          :rows="11"
          resize="none"
          maxlength="500"
          show-word-limit
          placeholder="请输入待分析的中文文本，例如：这家餐厅环境不错，服务也很热情。"
        />

        <div class="editor-panel__examples">
          <el-tag
            v-for="item in exampleTexts"
            :key="item.label"
            effect="plain"
            round
            class="editor-panel__example-tag"
            @click="fillExample(item.text)"
          >
            {{ item.label }} · {{ truncateText(item.text, 12) }}
          </el-tag>
        </div>

        <div class="editor-panel__actions">
          <el-button type="primary" size="large" :icon="MagicStick" :loading="loading" @click="handlePredict">
            开始分析
          </el-button>
          <el-button size="large" :icon="Delete" @click="clearForm">清空</el-button>
        </div>
      </div>

      <div class="card-panel result-panel">
        <div class="result-panel__head">
          <div>
            <h3>分析结果</h3>
            <p>右侧从标签、概率和置信度三个层次呈现模型判断结果。</p>
          </div>
          <SentimentBadge v-if="result" :label="result.predicted_label" size="large" />
        </div>

        <div v-if="result" class="result-panel__body">
          <div class="result-panel__summary">
            <div class="result-panel__summary-item">
              <span>情感倾向</span>
              <strong>{{ result.predicted_label }}</strong>
            </div>
            <div class="result-panel__summary-item">
              <span>置信等级</span>
              <el-tag round :type="confidenceMeta.type">{{ confidenceMeta.label }}</el-tag>
            </div>
            <div class="result-panel__summary-item">
              <span>当前模型</span>
              <strong>{{ result.model_name }}</strong>
            </div>
          </div>

          <ChartCard
            title="置信度仪表盘"
            description="越接近 100%，说明模型对当前判断越有把握。"
            height="240px"
            :option="gaugeOption"
          />

          <div class="glass-panel">
            <ConfidenceBar
              label="综合置信度"
              :value="result.confidence"
              :status="confidenceMeta.label"
              :color="confidenceMeta.color"
            />
            <ConfidenceBar label="积极概率" :value="result.positive_score" color="#16a34a" />
            <ConfidenceBar label="消极概率" :value="result.negative_score" color="#ef4444" />
          </div>

          <div class="result-panel__explain">
            <div class="result-panel__explain-label">分析说明</div>
            <p>{{ analysisText }}</p>
            <div class="result-panel__confidence">
              置信度：{{ formatPercent(result.confidence, 2) }}
            </div>
          </div>
        </div>

        <el-empty
          v-else
          description="输入中文文本并点击“开始分析”后，将在这里展示情感判断结果。"
        />
      </div>
    </div>

    <div class="card-panel table-card">
      <div class="table-card__header">
        <div>
          <h3>最近分析记录</h3>
          <p>便于演示系统的实时预测能力以及历史数据沉淀效果。</p>
        </div>
      </div>
      <el-table :data="recentRecords" stripe empty-text="暂无历史分析记录">
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
        <el-table-column label="积极概率" width="110">
          <template #default="{ row }">{{ formatPercent(row.positive_score, 2) }}</template>
        </el-table-column>
        <el-table-column label="消极概率" width="110">
          <template #default="{ row }">{{ formatPercent(row.negative_score, 2) }}</template>
        </el-table-column>
        <el-table-column label="置信度" width="110">
          <template #default="{ row }">{{ formatPercent(row.confidence, 2) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="160" />
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.predict-grid {
  align-items: flex-start;
}

.editor-panel,
.result-panel {
  padding: 22px;
}

.editor-panel__head h3,
.result-panel__head h3 {
  margin: 0;
  font-size: 18px;
}

.editor-panel__head p,
.result-panel__head p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.editor-panel__examples {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.editor-panel__example-tag {
  cursor: pointer;
}

.editor-panel__actions {
  display: flex;
  gap: 12px;
  margin-top: 22px;
}

.result-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.result-panel__body {
  display: grid;
  gap: 18px;
}

.result-panel__summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.result-panel__summary-item {
  padding: 16px;
  border-radius: 18px;
  background: rgba(245, 247, 251, 0.9);
}

.result-panel__summary-item span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
}

.result-panel__summary-item strong {
  display: block;
  margin-top: 10px;
  color: var(--text-primary);
  line-height: 1.6;
}

.result-panel__explain {
  padding: 18px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(47, 107, 255, 0.06), rgba(255, 255, 255, 0.95));
}

.result-panel__explain-label {
  font-size: 13px;
  color: #295df4;
  font-weight: 700;
}

.result-panel__explain p {
  margin: 10px 0 0;
  line-height: 1.8;
  color: var(--text-primary);
}

.result-panel__confidence {
  margin-top: 12px;
  color: var(--text-secondary);
}

.example-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

@media (max-width: 1200px) {
  .result-panel__summary {
    grid-template-columns: 1fr;
  }
}
</style>
