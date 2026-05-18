<script setup>
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
})
</script>

<template>
  <div class="confidence-bar">
    <div class="confidence-bar__head">
      <span>{{ label }}</span>
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
}

.confidence-bar__head strong {
  color: var(--text-primary);
  font-family: var(--number-font);
}
</style>
