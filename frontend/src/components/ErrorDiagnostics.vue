<script setup>
import { ref } from 'vue'

defineProps({
  errors: {
    type: Array,
    default: () => []
  }
})

const copiedIndex = ref(null)

function copyText(text, idx) {
  navigator.clipboard.writeText(text)
  copiedIndex.value = idx
  setTimeout(() => {
    copiedIndex.value = null
  }, 1800)
}
</script>

<template>
  <div class="diagnostics-module">
    <div class="diagnostics-header">
      <div class="header-main">
        <h3 class="diagnostics-title">语病诊断</h3>
        <span class="count-tag" v-if="errors.length > 0">{{ errors.length }} 处问题</span>
        <span class="count-tag clean" v-else>未检出语病</span>
      </div>
    </div>

    <!-- 无语病理想状态 -->
    <div v-if="errors.length === 0" class="clean-grammar-card">
      <div class="clean-check-icon">✓</div>
      <div class="clean-text-wrap">
        <h4>未检出明显语病</h4>
        <p>语法与词句规范达标。</p>
      </div>
    </div>

    <!-- 语病条目列表 -->
    <div v-else class="diagnostics-stream">
      <div
        v-for="(err, idx) in errors"
        :key="idx"
        class="diagnostic-card animate-fade-in"
      >
        <div class="card-meta-bar">
          <span class="type-pill">{{ err.error_type || '语言规范' }}</span>
          <span class="entry-index">#{{ idx + 1 }}</span>
        </div>

        <!-- 对比展示区 -->
        <div class="diff-container">
          <div class="diff-row original-row">
            <span class="diff-label">考生原句：</span>
            <span class="strike-content">{{ err.original_text }}</span>
          </div>

          <div class="diff-row correction-row">
            <span class="diff-label">标准升格：</span>
            <span class="correct-content">{{ err.correction }}</span>
            <button
              type="button"
              class="copy-correction-btn"
              :title="copiedIndex === idx ? '已复制' : '复制规范表达'"
              @click="copyText(err.correction, idx)"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span>{{ copiedIndex === idx ? '已复制' : '复制' }}</span>
            </button>
          </div>
        </div>

        <!-- 语法机理深度解析 -->
        <div class="rationale-box">
          <div class="quill-dot"></div>
          <p class="rationale-text">{{ err.explanation }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.diagnostics-module {
  margin-bottom: 2rem;
}

.diagnostics-header {
  margin-bottom: 1.25rem;
}

.header-main {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 0.25rem;
}

.diagnostics-title {
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-ink);
}

.count-tag {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.15rem 0.55rem;
  border-radius: var(--radius-full);
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.count-tag.clean {
  background: #f0fdf4;
  color: #15803d;
  border-color: #bbf7d0;
}

.diagnostics-sub {
  font-size: 0.82rem;
  color: var(--text-secondary);
}

.clean-grammar-card {
  background: var(--paper-card);
  border: 1px solid #bbf7d0;
  border-radius: var(--radius-lg);
  padding: 2rem;
  display: flex;
  align-items: center;
  gap: 1.25rem;
  box-shadow: var(--shadow-sm);
}

.clean-check-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #f0fdf4;
  color: #15803d;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  font-weight: 800;
  flex-shrink: 0;
}

.clean-text-wrap h4 {
  font-family: var(--font-display);
  font-size: 0.96rem;
  color: #166534;
  margin-bottom: 0.25rem;
}

.clean-text-wrap p {
  font-size: 0.84rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.diagnostics-stream {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.diagnostic-card {
  background: var(--paper-card);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  box-shadow: var(--shadow-sm);
  transition: all 0.18s ease;
}

.diagnostic-card:hover {
  border-color: var(--slate-mid);
  box-shadow: var(--shadow-md);
}

.card-meta-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.85rem;
}

.type-pill {
  font-size: 0.76rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: var(--radius-xs);
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.entry-index {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-muted);
}

.diff-container {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  background: var(--paper-warm);
  border: 1px solid var(--paper-border-soft);
  padding: 0.95rem 1.15rem;
  border-radius: var(--radius-sm);
  margin-bottom: 0.85rem;
}

.diff-row {
  display: flex;
  align-items: baseline;
  gap: 0.6rem;
  font-size: 0.92rem;
}

.diff-label {
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--text-muted);
  width: 68px;
  flex-shrink: 0;
}

.strike-content {
  color: #b91c1c;
  text-decoration: line-through;
  font-family: var(--font-body);
  font-weight: 500;
}

.correction-row {
  align-items: center;
}

.correct-content {
  color: #15803d;
  font-weight: 600;
  font-family: var(--font-body);
}

.copy-correction-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: var(--paper-subtle);
  border: 1px solid var(--paper-border);
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.74rem;
  margin-left: auto;
  transition: all 0.15s ease;
}

.copy-correction-btn:hover {
  background: #ffffff;
  color: var(--text-ink);
  border-color: var(--ink);
}

.rationale-box {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  font-size: 0.84rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.quill-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--amber);
  flex-shrink: 0;
  margin-top: 6px;
}

.rationale-text {
  flex: 1;
}
</style>
