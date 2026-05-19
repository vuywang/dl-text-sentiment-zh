<script setup>
import { Refresh } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import { activateModel, getModels } from '../api/model'
import PageHeader from '../components/PageHeader.vue'
import { useAppStore } from '../stores/app'
import { formatPercent } from '../utils/format'

const appStore = useAppStore()
const loading = ref(false)
const models = ref([])
const detailVisible = ref(false)
const detailRow = ref(null)

async function loadModels() {
  loading.value = true
  try {
    models.value = await getModels()
  } finally {
    loading.value = false
  }
}

async function handleActivate(row) {
  await ElMessageBox.confirm(`确认将模型“${row.model_name}”设为当前启用模型吗？`, '启用模型', {
    type: 'warning',
  })
  await activateModel(row.id)
  await Promise.all([loadModels(), appStore.fetchSummary()])
}

function openDetail(row) {
  detailRow.value = row
  detailVisible.value = true
}

onMounted(loadModels)
</script>

<template>
  <div class="page-grid">
    <PageHeader
      title="模型管理"
      description="基于 model_registry 和训练任务指标展示模型列表、启用状态、路径信息以及主要评估结果。"
      tag="Model Registry"
    >
      <el-button type="primary" plain :icon="Refresh" @click="loadModels">刷新模型列表</el-button>
    </PageHeader>

    <div class="card-panel table-card">
      <div class="table-card__header">
        <div>
          <h3>模型列表</h3>
          <p>保留“启用 / 查看指标”两个核心操作，不改动原有模型加载主逻辑。</p>
        </div>
      </div>
      <el-table v-loading="loading" :data="models" stripe empty-text="暂无模型注册记录">
        <el-table-column prop="model_name" label="模型名称" min-width="240" />
        <el-table-column prop="model_type" label="模型类型" width="110" />
        <el-table-column prop="model_dir" label="模型路径" min-width="320" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" min-width="160" />
        <el-table-column label="是否当前启用" width="110">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '当前启用' : '未启用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="220" show-overflow-tooltip />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" :disabled="row.is_active" @click="handleActivate(row)">
              启用
            </el-button>
            <el-button text @click="openDetail(row)">查看指标</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="detailVisible" width="760px" title="模型指标详情">
      <el-descriptions v-if="detailRow" :column="2" border>
        <el-descriptions-item label="模型名称">{{ detailRow.model_name }}</el-descriptions-item>
        <el-descriptions-item label="模型类型">{{ detailRow.model_type }}</el-descriptions-item>
        <el-descriptions-item label="Accuracy">{{ detailRow.accuracy == null ? '--' : formatPercent(detailRow.accuracy, 2) }}</el-descriptions-item>
        <el-descriptions-item label="Precision">{{ detailRow.precision == null ? '--' : formatPercent(detailRow.precision, 2) }}</el-descriptions-item>
        <el-descriptions-item label="Recall">{{ detailRow.recall == null ? '--' : formatPercent(detailRow.recall, 2) }}</el-descriptions-item>
        <el-descriptions-item label="F1-score">{{ detailRow.f1_score == null ? '--' : formatPercent(detailRow.f1_score, 2) }}</el-descriptions-item>
        <el-descriptions-item label="模型路径" :span="2">{{ detailRow.model_dir }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ detailRow.remark || '无' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>
