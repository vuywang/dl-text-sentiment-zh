<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    default: '',
  },
  value: {
    type: Number,
    default: 0,
  },
  color: {
    type: String,
    default: '#2f6bff',
  },
  status: {
    type: String,
    default: '',
  },
})

const statusType = computed(() => {
  if (props.status === '高可信') {
    return 'success'
  }
  if (props.status === '一般可信') {
    return 'warning'
  }
  if (props.status) {
    return 'danger'
  }
  return 'info'
})
</script>

<template>
  <div class="confidence-bar">
    <div class="confidence-bar__head">
      <div class="confidence-bar__label">
        <span>{{ label }}</span>
        <el-tag v-if="status" round effect="light" :type="statusType">{{ status }}</el-tag>
      </div>
      <strong>{{ (value * 100).toFixed(2) }}%</strong>
    </div>
    <el-progress
      :percentage="Number((value * 100).toFixed(2))"
      :stroke-width="12"
      :show-text="false"
      :color="color"
    />
  </div>
</template>

<style scoped>
.confidence-bar + .confidence-bar {
  margin-top: 18px;
}

.confidence-bar__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  color: var(--text-secondary);
  gap: 12px;
}

.confidence-bar__label {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.confidence-bar__head strong {
  color: var(--text-primary);
  font-family: var(--number-font);
}
</style>
