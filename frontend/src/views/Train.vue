<script setup>
import { Document, Promotion, Refresh } from '@element-plus/icons-vue'
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { getTrainHistory } from '../api/history'
import { getTrainLog, getTrainTask, startTraining } from '../api/train'
import PageHeader from '../components/PageHeader.vue'
import { useAppStore } from '../stores/app'

const appStore = useAppStore()
const form = reactive({
  epoch: 1,
  batch_size: 8,
  learning_rate: 0.00002,
  max_length: 64,
})

const historyList = ref([])
const currentTask = ref(null)
const submitting = ref(false)
const logVisible = ref(false)
const logLoading = ref(false)
const logContent = ref('')
const logTitle = ref('')

let pollTimer = 0

async function loadHistory() {
  historyList.value = await getTrainHistory()
  if (!currentTask.value && historyList.value.length) {
    currentTask.value = historyList.value[0]
  }
}

async function refreshCurrentTask() {
  const runningTask = currentTask.value?.status === 'running'
    ? currentTask.value
    : historyList.value.find((item) => item.status === 'running')
  if (!runningTask) {
    return
  }
  const latest = await getTrainTask(runningTask.id)
  currentTask.value = latest
  await loadHistory()
  if (latest.status !== 'running') {
    await appStore.fetchSummary()
  }
}

async function handleStart() {
  submitting.value = true
  try {
    currentTask.value = await startTraining(form)
    await loadHistory()
    if (!pollTimer) {
      pollTimer = window.setInterval(refreshCurrentTask, 5000)
    }
  } finally {
    submitting.value = false
  }
}

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

onMounted(async () => {
  await loadHistory()
  pollTimer = window.setInterval(refreshCurrentTask, 5000)
})

onBeforeUnmount(() => {
  if (pollTimer) {
    window.clearInterval(pollTimer)
  }
})
</script>

<template>
  <div class="page-grid">
    <PageHeader
      title="模型训练管理"
      description="保留原有 FastAPI 训练逻辑，通过可视化表单、状态卡片和日志入口增强答辩展示效果。"
      tag="Training Center"
    >
      <el-alert
        title="建议答辩时使用 epoch=1、batch_size=8、max_length=64 进行演示，不建议现场长时间训练。"
        type="warning"
        :closable="false"
      />
    </PageHeader>

    <div class="two-col-grid">
      <div class="card-panel form-panel">
        <div class="form-panel__head">
          <div>
            <h3>训练参数表单</h3>
            <p>参数保持简洁，便于答辩时清楚说明模型训练入口与核心超参数。</p>
          </div>
        </div>

        <el-form label-position="top" class="form-panel__form">
          <el-form-item label="epoch">
            <el-input-number v-model="form.epoch" :min="1" :max="20" />
          </el-form-item>
          <el-form-item label="batch_size">
            <el-input-number v-model="form.batch_size" :min="1" :max="128" />
          </el-form-item>
          <el-form-item label="learning_rate">
            <el-input-number
              v-model="form.learning_rate"
              :min="0.000001"
              :max="0.1"
              :step="0.00001"
              :precision="6"
              controls-position="right"
            />
          </el-form-item>
          <el-form-item label="max_length">
            <el-input-number v-model="form.max_length" :min="16" :max="512" />
          </el-form-item>
        </el-form>

        <div class="form-panel__actions">
          <el-button type="primary" size="large" :icon="Promotion" :loading="submitting" @click="handleStart">
            开始训练
          </el-button>
          <el-button size="large" :icon="Refresh" @click="loadHistory">刷新记录</el-button>
        </div>
      </div>

      <div class="card-panel status-panel">
        <div class="status-panel__head">
          <div>
            <h3>训练任务状态</h3>
            <p>实时展示最近任务的状态、指标与训练参数。</p>
          </div>
        </div>

        <template v-if="currentTask">
          <div class="status-item">
            <span>模型名称</span>
            <strong>{{ currentTask.model_name }}</strong>
          </div>
          <div class="status-item">
            <span>任务状态</span>
            <el-tag :type="currentTask.status === 'completed' ? 'success' : currentTask.status === 'failed' ? 'danger' : 'warning'">
              {{ currentTask.status }}
            </el-tag>
          </div>
          <div class="status-item">
            <span>参数配置</span>
            <strong>epoch={{ currentTask.epoch_count }} / batch_size={{ currentTask.batch_size }} / max_length={{ currentTask.max_length }}</strong>
          </div>
          <div class="status-item">
            <span>评估指标</span>
            <strong>Accuracy={{ currentTask.accuracy ?? '--' }}，F1={{ currentTask.f1_score ?? '--' }}</strong>
          </div>
          <div class="status-item">
            <span>时间信息</span>
            <strong>{{ currentTask.created_at }} ~ {{ currentTask.finished_at || '运行中' }}</strong>
          </div>
        </template>
        <el-empty v-else description="暂无训练任务记录" />
      </div>
    </div>

    <div class="card-panel table-card">
      <div class="table-card__header">
        <div>
          <h3>最近训练记录</h3>
          <p>重点保留训练任务状态、主要超参数、Accuracy 和日志查看入口。</p>
        </div>
      </div>
      <el-table :data="historyList" stripe empty-text="暂无训练任务记录">
        <el-table-column prop="model_name" label="模型名称" min-width="240" />
        <el-table-column prop="epoch_count" label="epoch" width="90" />
        <el-table-column prop="batch_size" label="batch_size" width="110" />
        <el-table-column prop="learning_rate" label="learning_rate" width="130" />
        <el-table-column prop="max_length" label="max_length" width="110" />
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="accuracy" label="Accuracy" width="110" />
        <el-table-column prop="created_at" label="创建时间" min-width="160" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button text type="primary" :icon="Document" @click="openLog(row)">查看日志</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="logVisible" width="900px" :title="`训练日志：${logTitle}`">
      <el-skeleton v-if="logLoading" animated :rows="8" />
      <pre v-else class="log-content">{{ logContent }}</pre>
    </el-dialog>
  </div>
</template>

<style scoped>
.form-panel,
.status-panel {
  padding: 22px;
}

.form-panel__head h3,
.status-panel__head h3 {
  margin: 0;
  font-size: 18px;
}

.form-panel__head p,
.status-panel__head p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.form-panel__form {
  margin-top: 20px;
}

.form-panel__actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.status-panel {
  display: grid;
  align-content: start;
  gap: 14px;
}

.status-item {
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(245, 247, 251, 0.92);
}

.status-item span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
}

.status-item strong {
  display: block;
  margin-top: 10px;
  line-height: 1.7;
  color: var(--text-primary);
}

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
