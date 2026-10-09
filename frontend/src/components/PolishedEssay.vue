<script setup>
import { ref } from 'vue'

const props = defineProps({
  originalEssay: {
    type: String,
    default: ''
  },
  polishedEssay: {
    type: String,
    default: ''
  }
})

const activeTab = ref('polished')
const copied = ref(false)

function copyEssay() {
  if (!props.polishedEssay) return
  navigator.clipboard.writeText(props.polishedEssay)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}
</script>

<template>
  <div class="polished-paper-module animate-fade-in">
    <div class="module-header-row">
      <div class="title-cluster">
        <div class="quill-insignia">✦</div>
        <div>
          <h3 class="module-title">升格示范范文</h3>
        </div>
      </div>

      <div class="header-actions">
        <div class="view-switch-tabs">
          <button
            type="button"
            class="switch-btn"
            :class="{ active: activeTab === 'polished' }"
            @click="activeTab = 'polished'"
          >
            升格范本
          </button>
          <button
            type="button"
            class="switch-btn"
            :class="{ active: activeTab === 'compare' }"
            @click="activeTab = 'compare'"
          >
            原著对照
          </button>
        </div>

        <button type="button" class="copy-essay-cta" @click="copyEssay">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          <span>{{ copied ? '已复制范文！' : '复制范文' }}</span>
        </button>
      </div>
    </div>

    <!-- 单栏满宽研读模式 -->
    <div v-if="activeTab === 'polished'" class="single-paper-container">
      <div class="manuscript-sheet">
        <div class="sheet-watermark">BAND FIVE EXEMPLAR</div>
        <pre class="manuscript-text">{{ polishedEssay }}</pre>
      </div>
    </div>

    <!-- 双栏对照模式 -->
    <div v-else class="compare-columns-grid">
      <div class="compare-column">
        <div class="col-tab-bar draft">
          <span>考生原始作答 (Draft)</span>
        </div>
        <div class="manuscript-sheet draft-sheet">
          <pre class="manuscript-text">{{ originalEssay }}</pre>
        </div>
      </div>

      <div class="compare-column">
        <div class="col-tab-bar polished">
          <span>第五档卓越升格范本 (Exemplar)</span>
        </div>
        <div class="manuscript-sheet exemplar-sheet">
          <pre class="manuscript-text">{{ polishedEssay }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.polished-paper-module {
  background: var(--paper-card);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.module-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.25rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--paper-border-soft);
}

.title-cluster {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.quill-insignia {
  font-size: 1.15rem;
  color: var(--amber);
  display: flex;
  align-items: center;
  justify-content: center;
}

.module-title {
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-ink);
}

.module-subtitle {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.view-switch-tabs {
  display: inline-flex;
  background: var(--paper-subtle);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-md);
  padding: 2px;
}

.switch-btn {
  padding: 0.35rem 0.75rem;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.18s ease;
}

.switch-btn.active {
  background: #ffffff;
  color: var(--text-ink);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(12, 18, 34, 0.08);
}

.copy-essay-cta {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.85rem;
  background: var(--paper-warm);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-ink);
  cursor: pointer;
  transition: all 0.18s ease;
}

.copy-essay-cta:hover {
  background: #ffffff;
  border-color: var(--ink);
}

/* ── 稿纸样式 ── */
.manuscript-sheet {
  background: var(--paper-warm);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-md);
  padding: 1.5rem 1.75rem;
  position: relative;
  overflow: hidden;
}

.sheet-watermark {
  position: absolute;
  top: 1rem;
  right: 1.25rem;
  font-family: var(--font-display);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: var(--paper-border);
  pointer-events: none;
  user-select: none;
}

.manuscript-text {
  font-family: var(--font-body);
  font-size: 0.98rem;
  line-height: 1.85;
  color: var(--text-ink);
  white-space: pre-wrap;
  word-break: break-word;
  position: relative;
  z-index: 1;
}

/* ── 双栏对照 ── */
.compare-columns-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}

.compare-column {
  display: flex;
  flex-direction: column;
}

.col-tab-bar {
  font-size: 0.78rem;
  font-weight: 700;
  padding: 0.4rem 0.85rem;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  margin-bottom: -1px;
}

.col-tab-bar.draft {
  background: var(--paper-subtle);
  color: var(--text-secondary);
  border: 1px solid var(--paper-border);
  border-bottom: none;
}

.col-tab-bar.polished {
  background: var(--ink);
  color: var(--paper);
  border: 1px solid var(--ink);
  border-bottom: none;
}

.draft-sheet {
  border-radius: 0 0 var(--radius-md) var(--radius-md);
  background: var(--paper-subtle);
}

.exemplar-sheet {
  border-radius: 0 0 var(--radius-md) var(--radius-md);
  background: var(--paper-warm);
  border-color: var(--ink);
}

@media (max-width: 860px) {
  .compare-columns-grid {
    grid-template-columns: 1fr;
  }
}
</style>
