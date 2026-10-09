<script setup>
defineProps({
  deductions: {
    type: Array,
    default: () => []
  },
  highlights: {
    type: Array,
    default: () => []
  },
  suggestions: {
    type: Array,
    default: () => []
  }
})
</script>

<template>
  <div class="analysis-triptych">
    <!-- 1. 大纲扣分细则 -->
    <div class="triptych-column deductions-col">
      <div class="column-header">
        <div class="icon-box danger">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
        </div>
        <div class="header-text">
          <h4 class="column-title">大纲扣分项</h4>
        </div>
      </div>

      <div v-if="deductions.length === 0" class="status-empty-box success">
        <span class="empty-icon">✓</span>
        <span>未触发大纲扣分</span>
      </div>

      <div v-else class="entries-stream">
        <div v-for="(d, idx) in deductions" :key="idx" class="entry-card deduction">
          <div class="entry-top">
            <span class="entry-title danger">{{ d.item }}</span>
            <span class="penalty-tag">-{{ d.points }} 分</span>
          </div>
          <p class="entry-body">{{ d.rule }}</p>
        </div>
      </div>
    </div>

    <!-- 2. 亮点表达与加分项 -->
    <div class="triptych-column highlights-col">
      <div class="column-header">
        <div class="icon-box success">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
          </svg>
        </div>
        <div class="header-text">
          <h4 class="column-title">亮点表达</h4>
        </div>
      </div>

      <div v-if="highlights.length === 0" class="status-empty-box neutral">
        <span>暂无明显亮点</span>
      </div>

      <div v-else class="entries-stream">
        <div v-for="(h, idx) in highlights" :key="idx" class="entry-card highlight">
          <div class="quote-container">
            <span class="quote-mark">“</span>
            <span class="quote-content">{{ h.quote }}</span>
            <span class="quote-mark">”</span>
          </div>
          <p class="entry-body">{{ h.praise }}</p>
        </div>
      </div>
    </div>

    <!-- 3. 提分建议 -->
    <div class="triptych-column suggestions-col">
      <div class="column-header">
        <div class="icon-box primary">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
          </svg>
        </div>
        <div class="header-text">
          <h4 class="column-title">提分建议</h4>
        </div>
      </div>

      <div class="entries-stream">
        <div v-for="(sug, idx) in suggestions" :key="idx" class="entry-card suggestion">
          <div class="index-num">{{ idx + 1 }}</div>
          <p class="entry-body">{{ sug }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.analysis-triptych {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.25rem;
  margin-bottom: 2rem;
}

.triptych-column {
  background: var(--paper-card);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
}

.column-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--paper-border-soft);
}

.icon-box {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-box.danger {
  background: #fef2f2;
  color: #b91c1c;
}

.icon-box.success {
  background: #f0fdf4;
  color: #15803d;
}

.icon-box.primary {
  background: var(--paper-subtle);
  color: var(--text-ink);
}

.column-title {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-ink);
}

.column-desc {
  font-size: 0.74rem;
  color: var(--text-muted);
}

.status-empty-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.82rem;
  padding: 0.85rem 1rem;
  border-radius: var(--radius-sm);
  margin: auto 0;
}

.status-empty-box.success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.status-empty-box.neutral {
  background: var(--paper-warm);
  color: var(--text-muted);
  border: 1px dashed var(--paper-border);
}

.entries-stream {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.entry-card {
  padding: 0.85rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--paper-border-soft);
}

.entry-card.deduction {
  background: #fef2f2;
  border-color: #fecaca;
}

.entry-card.highlight {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.entry-card.suggestion {
  background: var(--paper-warm);
  border-color: var(--paper-border);
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
}

.entry-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.35rem;
}

.entry-title {
  font-size: 0.86rem;
  font-weight: 700;
}

.entry-title.danger {
  color: #991b1b;
}

.penalty-tag {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  font-weight: 700;
  color: #ffffff;
  background: #b91c1c;
  padding: 0.1rem 0.45rem;
  border-radius: 3px;
}

.quote-container {
  margin-bottom: 0.35rem;
  color: #166534;
  font-weight: 600;
  font-size: 0.88rem;
}

.quote-mark {
  color: #15803d;
  font-weight: 700;
}

.index-num {
  font-family: var(--font-mono);
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--ink);
  color: var(--paper);
  font-size: 0.72rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.entry-body {
  font-size: 0.82rem;
  line-height: 1.55;
  color: var(--text-body);
}

@media (max-width: 1024px) {
  .analysis-triptych {
    grid-template-columns: 1fr;
  }
}
</style>
