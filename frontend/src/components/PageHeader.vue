<script setup>
defineProps({
  title: {
    type: String,
    default: '',
  },
  description: {
    type: String,
    default: '',
  },
  tag: {
    type: String,
    default: '',
  },
})
</script>

<template>
  <div class="page-header card-panel">
    <div>
      <div v-if="tag" class="page-header__tag">{{ tag }}</div>
      <h2>{{ title }}</h2>
      <p>{{ description }}</p>
    </div>
    <div class="page-header__extra">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 24px;
  margin-bottom: 22px;
  background:
    linear-gradient(135deg, rgba(47, 107, 255, 0.12), rgba(255, 255, 255, 0.96)),
    #ffffff;
}

.page-header__tag {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(47, 107, 255, 0.1);
  color: #295df4;
  font-size: 12px;
  margin-bottom: 14px;
}

.page-header h2 {
  margin: 0;
  font-size: 28px;
  font-family: var(--heading-font);
  color: var(--text-primary);
}

.page-header p {
  margin: 10px 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.page-header__extra {
  margin-left: auto;
}

@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .page-header__extra {
    margin-left: 0;
    width: 100%;
  }
}
</style>
