<script setup>
defineProps({
  show: Boolean,
  reports: {
    type: Array,
    default: () => []
  }
})

defineEmits(['close', 'selectReport'])

function formatDate(mtime) {
  if (!mtime) return ''
  const d = new Date(mtime * 1000)
  return d.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<template>
  <div v-if="show" class="drawer-backdrop" @click.self="$emit('close')">
    <div class="drawer-panel animate-fade-in">
      <div class="drawer-header">
        <div class="header-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          <h3>评卷归档历史</h3>
        </div>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <div class="drawer-body">
        <div v-if="reports.length === 0" class="empty-notice">
          <p>暂无历史评卷归档报告</p>
        </div>

        <div v-else class="reports-list">
          <div
            v-for="(r, idx) in reports"
            :key="idx"
            class="report-card"
            @click="$emit('selectReport', r.filename)"
          >
            <div class="report-meta-top">
              <span class="report-tag" :class="r.filename.includes('小作文') ? 'small' : 'big'">
                {{ r.filename.includes('小作文') ? 'Part A 小作文' : 'Part B 大作文' }}
              </span>
              <span class="report-time">{{ formatDate(r.mtime) }}</span>
            </div>
            <div class="report-filename">{{ r.filename }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(12, 18, 34, 0.5);
  backdrop-filter: blur(5px);
  z-index: 100;
  display: flex;
  justify-content: flex-end;
}

.drawer-panel {
  width: 440px;
  max-width: 92vw;
  height: 100%;
  background: var(--paper-warm);
  box-shadow: var(--shadow-xl);
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--paper-border);
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--paper-border);
  background: var(--paper-card);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-ink);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.15rem;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
}
.close-btn:hover { color: var(--text-ink); }

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem 1.5rem;
}

.empty-notice {
  text-align: center;
  color: var(--text-muted);
  font-size: 0.88rem;
  margin-top: 3.5rem;
}

.reports-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.report-card {
  padding: 0.95rem 1.1rem;
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-md);
  background: var(--paper-card);
  cursor: pointer;
  transition: all 0.18s ease;
}

.report-card:hover {
  border-color: var(--ink);
  transform: translateX(-2px);
  box-shadow: var(--shadow-sm);
}

.report-meta-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.45rem;
}

.report-tag {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
}

.report-tag.small {
  background: #eff6ff;
  color: #1d4ed8;
}

.report-tag.big {
  background: #f5f3ff;
  color: #6d28d9;
}

.report-time {
  font-family: var(--font-mono);
  font-size: 0.74rem;
  color: var(--text-muted);
}

.report-filename {
  font-size: 0.82rem;
  color: var(--text-ink);
  word-break: break-all;
  font-family: var(--font-mono);
  line-height: 1.45;
}
</style>
