<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const currentStep = ref(0)
const steps = [
  { title: '篇章结构与词数预检', desc: '检查字数与基础格式规范' },
  { title: '知识库标准比对', desc: '检索官方大纲档次与同类真题范文' },
  { title: '核心维度量化评卷', desc: '按内容、组织、语言与规范综合打分' },
  { title: '语病诊断与升格润色', desc: '分析典型语病并生成高分示范范文' }
]

let timer = null

onMounted(() => {
  timer = setInterval(() => {
    if (currentStep.value < steps.length - 1) {
      currentStep.value++
    }
  }, 2200)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="eval-modal-backdrop">
    <div class="eval-modal-sheet animate-fade-in-scale">
      <div class="eval-head">
        <div class="pulsing-halo">
          <div class="halo-core">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
          </div>
        </div>
        <h3 class="eval-title">正在智能评卷</h3>
        <p class="eval-subtitle">对照考纲评分标准进行多维度分析</p>
      </div>

      <div class="eval-timeline">
        <div
          v-for="(step, idx) in steps"
          :key="idx"
          class="timeline-node"
          :class="{
            active: idx === currentStep,
            completed: idx < currentStep,
            pending: idx > currentStep
          }"
        >
          <div class="node-bullet">
            <template v-if="idx < currentStep">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </template>
            <template v-else-if="idx === currentStep">
              <span class="micro-spin"></span>
            </template>
            <template v-else>
              <span>{{ idx + 1 }}</span>
            </template>
          </div>
          <div class="node-text">
            <div class="node-title">{{ step.title }}</div>
            <div class="node-desc">{{ step.desc }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.eval-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(12, 18, 34, 0.72);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 1.5rem;
}

.eval-modal-sheet {
  background: var(--paper-warm);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  max-width: 480px;
  width: 100%;
  padding: 2.25rem 2rem;
  border: 1px solid rgba(12, 18, 34, 0.12);
}

.eval-head {
  text-align: center;
  margin-bottom: 2rem;
}

.pulsing-halo {
  width: 54px;
  height: 54px;
  margin: 0 auto 1.25rem;
  border-radius: 50%;
  background: var(--paper-subtle);
  border: 1px solid var(--paper-border);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.pulsing-halo::after {
  content: '';
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  border: 2px solid var(--amber);
  opacity: 0.35;
  animation: pulse-ring 2s cubic-bezier(0.24, 0, 0.38, 1) infinite;
}

.halo-core {
  color: var(--amber);
  display: flex;
  align-items: center;
  justify-content: center;
}

.eval-title {
  font-family: var(--font-display);
  font-size: 1.18rem;
  font-weight: 700;
  color: var(--text-ink);
  margin-bottom: 0.35rem;
}

.eval-subtitle {
  font-size: 0.82rem;
  color: var(--text-secondary);
}

.eval-timeline {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.timeline-node {
  display: flex;
  align-items: flex-start;
  gap: 0.9rem;
  opacity: 0.45;
  transition: all 0.3s ease;
}

.timeline-node.active {
  opacity: 1;
}

.timeline-node.completed {
  opacity: 0.85;
}

.node-bullet {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-mono);
  font-size: 0.78rem;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 1px;
}

.timeline-node.pending .node-bullet {
  background: var(--paper-subtle);
  color: var(--text-muted);
  border: 1px solid var(--paper-border);
}

.timeline-node.active .node-bullet {
  background: var(--ink);
  color: var(--paper);
  box-shadow: 0 0 0 3px rgba(12, 18, 34, 0.15);
}

.timeline-node.completed .node-bullet {
  background: var(--success);
  color: #ffffff;
}

.node-title {
  font-family: var(--font-display);
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-ink);
  margin-bottom: 0.15rem;
}

.node-desc {
  font-size: 0.76rem;
  color: var(--text-secondary);
  line-height: 1.45;
}

.micro-spin {
  width: 11px;
  height: 11px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
</style>
