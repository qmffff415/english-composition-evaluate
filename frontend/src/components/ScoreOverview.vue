<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    required: true
  }
})

const scorePercentage = computed(() => {
  const total = Number(props.result.total_score) || 0
  const max = Number(props.result.max_score) || 10
  return Math.min(100, Math.max(0, Math.round((total / max) * 100)))
})

const scoreTheme = computed(() => {
  const p = scorePercentage.value
  if (p >= 85) return { color: 'band-first', label: '第五档 · 极佳', desc: '语言地道，紧扣题意，结构严谨' }
  if (p >= 70) return { color: 'band-second', label: '第四档 · 良好', desc: '表达清晰，要点完整，稍有瑕疵' }
  if (p >= 50) return { color: 'band-third', label: '第三档 · 及格', desc: '基本切题，语法偶错，结构松散' }
  if (p >= 30) return { color: 'band-fourth', label: '第二档 · 偏弱', desc: '偏题或字数偏少，语病较明显' }
  return { color: 'band-fourth', label: '第一档 · 待提升', desc: '篇幅严重不足或跑题，不成篇章' }
})

const ragChunkCount = computed(() => {
  if (!props.result.meta?.rag_chunks_used) return 0
  if (typeof props.result.meta.rag_chunks_used === 'number') return props.result.meta.rag_chunks_used
  return Object.values(props.result.meta.rag_chunks_used).reduce((a, b) => a + (Number(b) || 0), 0)
})
</script>

<template>
  <div class="score-overview-sheet animate-fade-in">
    <!-- 顶部总分与档次主卡 -->
    <div class="score-hero-row">
      <!-- 醒目打分牌 -->
      <div class="score-seal-box" :class="scoreTheme.color">
        <div class="seal-inner">
          <div class="score-num-wrap">
            <span class="score-val">{{ result.total_score }}</span>
            <span class="score-total">/ {{ result.max_score }}</span>
          </div>
          <div class="band-title-pill">
            {{ result.band || scoreTheme.label }}
          </div>
        </div>
      </div>

      <!-- 评分条与评卷元数据 -->
      <div class="score-analytics">
        <div class="rate-bar-block">
          <div class="rate-label-row">
            <span class="rate-title">得分率</span>
            <span class="rate-number">{{ scorePercentage }}%</span>
          </div>
          <div class="rate-track">
            <div
              class="rate-fill"
              :class="scoreTheme.color"
              :style="{ width: `${scorePercentage}%` }"
            ></div>
          </div>
        </div>

        <div class="score-meta-grid">
          <div class="meta-item">
            <span class="meta-label">试卷类型</span>
            <span class="meta-value">{{ result.essay_type }} · {{ result.sub_type }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">实测词数</span>
            <span class="meta-value">{{ result.word_count }} 词</span>
          </div>
          <div class="meta-item" v-if="result.meta?.latency_seconds">
            <span class="meta-label">评卷耗时</span>
            <span class="meta-value">{{ result.meta.latency_seconds }} 秒</span>
          </div>
          <div class="meta-item" v-if="ragChunkCount">
            <span class="meta-label">知识库参考</span>
            <span class="meta-value">{{ ragChunkCount }} 条</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 阅卷组长综合裁定评语 -->
    <div class="examiner-memo">
      <div class="memo-header">
        <div class="memo-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 20h9"></path>
            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
          </svg>
        </div>
        <div class="memo-title-box">
          <h4 class="memo-title">阅卷总评</h4>
        </div>
      </div>
      <div class="memo-content">
        <p class="memo-text">{{ result.summary_comment }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.score-overview-sheet {
  background: var(--paper-card);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 1.75rem;
  margin-bottom: 2rem;
}

/* ── 顶部总分行 ── */
.score-hero-row {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding-bottom: 1.75rem;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid var(--paper-border-soft);
}

.score-seal-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 180px;
  padding: 1.5rem 1.25rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--paper-border);
  background: var(--paper-warm);
  position: relative;
}

.score-seal-box.band-first {
  background: linear-gradient(145deg, #f0fdf4 0%, #dcfce7 100%);
  border-color: #bbf7d0;
}
.score-seal-box.band-second {
  background: linear-gradient(145deg, #fefce8 0%, #fef3c7 100%);
  border-color: #fde68a;
}
.score-seal-box.band-third {
  background: linear-gradient(145deg, #fffbeb 0%, #fed7aa 100%);
  border-color: #fdba74;
}
.score-seal-box.band-fourth {
  background: linear-gradient(145deg, #fef2f2 0%, #fee2e2 100%);
  border-color: #fecaca;
}

.seal-inner {
  text-align: center;
}

.score-num-wrap {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 0.35rem;
  margin-bottom: 0.5rem;
}

.score-val {
  font-family: var(--font-display);
  font-size: 3.5rem;
  font-weight: 800;
  line-height: 1;
  color: var(--text-ink);
  letter-spacing: -0.04em;
}

.score-total {
  font-family: var(--font-mono);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-muted);
}

.band-title-pill {
  font-family: var(--font-display);
  font-size: 0.84rem;
  font-weight: 700;
  padding: 0.25rem 0.85rem;
  border-radius: var(--radius-full);
  display: inline-block;
  background: var(--ink);
  color: #ffffff;
  box-shadow: 0 2px 6px rgba(12, 18, 34, 0.15);
}

/* ── 右侧进度与元数据 ── */
.score-analytics {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.rate-bar-block {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.rate-label-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 0.86rem;
}

.rate-title {
  color: var(--text-secondary);
  font-weight: 600;
}

.rate-number {
  font-family: var(--font-mono);
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-ink);
}

.rate-track {
  height: 10px;
  background: var(--paper-subtle);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.rate-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.9s cubic-bezier(0.16, 1, 0.3, 1);
  background: var(--ink);
}

.rate-fill.band-first {
  background: linear-gradient(90deg, #15803d, #22c55e);
}
.rate-fill.band-second {
  background: linear-gradient(90deg, #d97706, #f59e0b);
}
.rate-fill.band-third {
  background: linear-gradient(90deg, #ea580c, #f97316);
}
.rate-fill.band-fourth {
  background: linear-gradient(90deg, #b91c1c, #ef4444);
}

.score-meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.75rem;
}

.meta-item {
  background: var(--paper-warm);
  border: 1px solid var(--paper-border-soft);
  border-radius: var(--radius-sm);
  padding: 0.55rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.meta-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-muted);
}

.meta-value {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--text-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── 阅卷组长综合评语 ── */
.examiner-memo {
  background: var(--paper-warm);
  border: 1px solid var(--paper-border);
  border-radius: var(--radius-md);
  padding: 1.25rem 1.5rem;
  position: relative;
}

.memo-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--paper-border-soft);
}

.memo-icon {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  background: var(--ink);
  color: var(--paper);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.memo-title-box {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.memo-title {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-ink);
}

.memo-subtitle {
  font-size: 0.76rem;
  color: var(--text-secondary);
}

.memo-content {
  font-size: 0.92rem;
  line-height: 1.8;
  color: var(--text-body);
}

.memo-text {
  letter-spacing: 0.01em;
}

@media (max-width: 768px) {
  .score-hero-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
