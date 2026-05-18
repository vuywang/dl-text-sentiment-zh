<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: 'default',
  },
})

const config = computed(() => {
  if (props.label === '积极') {
    return { type: 'success', text: '积极情感' }
  }
  if (props.label === '消极') {
    return { type: 'danger', text: '消极情感' }
  }
  return { type: 'info', text: props.label || '待分析' }
})
</script>

<template>
  <el-tag round effect="light" :type="config.type" :size="size">{{ config.text }}</el-tag>
</template>
