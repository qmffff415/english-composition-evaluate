<script setup>
defineProps({
  dimensions: {
    type: Object,
    default: () => ({})
  }
})

const dimensionIcons = {
  content: `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline>`,
  organization: `<rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line>`,
  language: `<path d="m5 8 6 6"></path><path d="m4 14 6-6 2-3"></path><path d="M2 5h12"></path><path d="M7 2h1"></path><path d="m22 22-5-10-5 10"></path><path d="M14 18h6"></path>`,
  format: `<rect x="2" y="4" width="20" height="16" rx="2"></rect><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>`
}

function getPct(score, maxScore) {
  const s = Number(score) || 0
  const ms = Number(maxScore) || 0
  if (ms <= 0) return 0
  return Math.min(100, Math.max(0, Math.round((s / ms) * 100)))
}
</script>

<template>
  <div class="dimensions-module">
    <div class="module-title-bar">
      <div class="title-cluster">
        <h3 class="module-heading">维度量化得分</h3>
      </div>
    </div>

    <div class="dimensions-cards-grid">
      <div
        v-for="(dim, key) in dimensions"
        :key="key"
        class="dim-metric-card animate-fade-in"
      >
        <div class="card-head">
          <div class="dim-badge-icon" :class="key">
            <svg
              width="17"
              height="17"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              v-html="dimensionIcons[key] || dimensionIcons.content"
            ></svg>
          </div>
          <div class="dim-head-info">
            <h4 class="dim-title">{{ dim.name }}</h4>
            <div class="score-pill">
              <span class="score-actual">{{ dim.score }}</span>
              <span class="score-limit">/ {{ dim.max_score }} 分</span>
            </div>
          </div>
        </div>

        <div class="bar-container">
          <div class="bar-track">
            <div
              class="bar-fill"
              :class="key"
              :style="{ width: `${getPct(dim.score, dim.max_score)}%` }"
            ></div>
          </div>
          <span class="bar-pct">{{ getPct(dim.score, dim.max_score) }}%</span>
        </div>

        <div class="card-body">
          <div class="rationale-chip" v-if="dim.score_reason">
            <span class="rationale-tag">裁定依据</span>
            <span class="rationale-desc">{{ dim.score_reason }}</span>
          </div>
          <p class="analysis-prose">{{ dim.analysis }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dimensions-module {
  margin-bottom: 2rem;
}

.module-title-bar {
  margin-bottom: 1.25rem;
}

.module-heading {
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-ink);
  margin-bottom: 0.2rem;
}

.module-sub {
  font-size: 0.82rem;
  color: var(--text-secondary);
}

.dimensions-cards-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.dim-metric-card {
  background: var(--paper-card);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 1.35rem;
  display: flex;
  flex-direction: column;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.dim-metric-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--slate-mid);
}

.card-head {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}

.dim-badge-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--paper-subtle);
  color: var(--text-ink);
}

.dim-badge-icon.content {
  background: #eff6ff;
  color: #1d4ed8;
}

.dim-badge-icon.organization {
  background: #f5f3ff;
  color: #6d28d9;
}

.dim-badge-icon.language {
  background: #fef3c7;
  color: #b45309;
}

.dim-badge-icon.format {
  background: #f0fdf4;
  color: #15803d;
}

.dim-head-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.dim-title {
  font-family: var(--font-display);
  font-size: 0.96rem;
  font-weight: 700;
  color: var(--text-ink);
}

.score-actual {
  font-family: var(--font-mono);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-ink);
}

.score-limit {
  font-size: 0.76rem;
  color: var(--text-muted);
  margin-left: 0.2rem;
}

.bar-container {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 0.85rem;
}

.bar-track {
  flex: 1;
  height: 6px;
  background: var(--paper-subtle);
  border-radius: 3px;
  overflow: hidden;
  border: 1px solid var(--paper-border-soft);
}

.bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.7s cubic-bezier(0.16, 1, 0.3, 1);
  background: var(--ink);
}

.bar-fill.content { background: #1d4ed8; }
.bar-fill.organization { background: #6d28d9; }
.bar-fill.language { background: #b45309; }
.bar-fill.format { background: #15803d; }

.bar-pct {
  font-family: var(--font-mono);
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--text-secondary);
  width: 32px;
  text-align: right;
}

.rationale-chip {
  background: var(--paper-warm);
  border: 1px solid var(--paper-border);
  padding: 0.45rem 0.65rem;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  margin-bottom: 0.65rem;
  display: flex;
  gap: 0.4rem;
  align-items: baseline;
}

.rationale-tag {
  font-weight: 700;
  color: var(--text-ink);
  white-space: nowrap;
}

.rationale-desc {
  color: var(--text-body);
}

.analysis-prose {
  font-size: 0.86rem;
  line-height: 1.65;
  color: var(--text-secondary);
}

@media (max-width: 860px) {
  .dimensions-cards-grid {
    grid-template-columns: 1fr;
  }
}
</style>
