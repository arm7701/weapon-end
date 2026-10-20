<template>
  <section v-if="selectedTargetId" class="detection-list-panel">
    <header class="panel-head">
      <div>
        <span class="kicker">BUILDING-SEG</span>
        <strong><i class="bi bi-buildings"></i> อาคาร Detection</strong>
      </div>
      <em>{{ filteredDetections.length }}</em>
    </header>

    <div class="detect-action-wrap">
      <div class="detect-controls-row">
        <label class="radius-select-label" title="รัศมีการตรวจจับรอบเป้าหมาย (ม.)">
          <i class="bi bi-bullseye"></i>
          <select v-model.number="selectedRadiusM" :disabled="detecting" class="radius-select">
            <option :value="50">50 ม.</option>
            <option :value="100">100 ม.</option>
            <option :value="120">120 ม. (มาตรฐาน)</option>
            <option :value="200">200 ม.</option>
            <option :value="300">300 ม.</option>
          </select>
        </label>
        <button
          type="button"
          class="run-detect-btn"
          :disabled="detecting || !selectedTargetId"
          :title="detecting ? 'กำลังจับภาพและประมวลผลโมเดล building-seg.pt' : 'ตรวจจับอาคารรอบเป้าหมายที่เลือก'"
          @click="onRunDetection"
        >
          <i class="bi" :class="detecting ? 'bi-hourglass-split spin' : 'bi-radar'"></i>
          <span>{{ detecting ? 'กำลังตรวจจับอาคาร…' : 'ตรวจจับอาคาร' }}</span>
        </button>
      </div>
    </div>

    <p v-if="!filteredDetections.length" class="empty">
      ยังไม่มีอาคาร detection ของเป้าหมายนี้
    </p>

    <div v-else class="object-list">
      <div
        v-for="item in filteredDetections"
        :key="item.id"
        class="object-row"
        :class="{ active: selectedObjectId === item.id }"
        @click="selectObject(item)"
      >
        <span class="risk-dot" :class="item.risk || 'low'"></span>
        <span class="object-copy">
          <strong>{{ item.label || item.objectType || 'Building' }}</strong>
          <small>
            {{ riskLabel(item.risk) }}
            <template v-if="item.confidence != null">
              · {{ Math.round(Number(item.confidence) * 100) }}%
            </template>
          </small>
        </span>
        <button
          type="button"
          class="delete-btn"
          title="ลบอาคารนี้"
          :disabled="deletingId === item.id"
          @click.stop="removeObject(item)"
        >
          <i class="bi" :class="deletingId === item.id ? 'bi-hourglass-split' : 'bi-trash'"></i>
        </button>
      </div>
    </div>

    <p v-if="message" class="hint">{{ message }}</p>
  </section>
</template>

<script>
import { computed, ref, watch } from 'vue'
import { deleteResource } from '../services/api'

const RISK_LABELS = {
  high: 'เสี่ยงสูง',
  medium: 'ปานกลาง',
  low: 'เสี่ยงต่ำ',
}

export default {
  name: 'TargetDetectionListPanel',
  props: {
    detections: { type: Array, default: () => [] },
    selectedTargetId: { type: String, default: '' },
    selectedCoordinateId: { type: String, default: '' },
    detecting: { type: Boolean, default: false },
  },
  emits: ['deleted', 'select-object', 'error', 'run-detection'],
  setup(props, { emit }) {
    const deletingId = ref('')
    const selectedObjectId = ref('')
    const message = ref('')
    const selectedRadiusM = ref(120)

    function onRunDetection() {
      message.value = 'กำลังจัดมุมกล้องและส่งตรวจจับอาคารด้วย building-seg.pt…'
      emit('run-detection', {
        radiusM: selectedRadiusM.value,
        coordinateId: props.selectedCoordinateId,
      })
    }

    watch(
      () => props.detecting,
      (isDetecting, wasDetecting) => {
        if (wasDetecting && !isDetecting) {
          if (filteredDetections.value.length > 0) {
            message.value = `ตรวจจับสำเร็จ (พบ ${filteredDetections.value.length} อาคาร)`
          } else {
            message.value = 'ตรวจจับเสร็จสิ้น (ไม่พบอาคารในรัศมีนี้)'
          }
        }
      },
    )

    const filteredDetections = computed(() => {
      const list = props.detections || []
      if (!props.selectedTargetId) return []
      let rows = list.filter((d) => d.targetCardId === props.selectedTargetId)
      if (props.selectedCoordinateId) {
        const scoped = rows.filter(
          (d) => d.targetCoordinateId === props.selectedCoordinateId,
        )
        if (scoped.length) rows = scoped
      }
      return rows
    })

    function riskLabel(risk) {
      return RISK_LABELS[risk] || risk || '—'
    }

    function selectObject(item) {
      selectedObjectId.value = item.id
      emit('select-object', item)
    }

    async function removeObject(item) {
      if (!item?.id || deletingId.value) return
      const label = item.label || 'อาคาร'
      const ok = window.confirm(`ลบ ${label} และคำนวณทิศทางเข้า-ออกใหม่?`)
      if (!ok) return
      deletingId.value = item.id
      message.value = ''
      try {
        await deleteResource('/detection-objects', item.id)
        if (selectedObjectId.value === item.id) selectedObjectId.value = ''
        message.value = `ลบ ${label} แล้ว`
        emit('deleted', item)
      } catch (err) {
        const text = err?.message || 'ลบอาคารไม่สำเร็จ'
        message.value = text
        emit('error', text)
      } finally {
        deletingId.value = ''
      }
    }

    watch(
      () => [props.selectedTargetId, props.selectedCoordinateId],
      () => {
        selectedObjectId.value = ''
        message.value = ''
      },
    )

    return {
      filteredDetections,
      deletingId,
      selectedObjectId,
      message,
      riskLabel,
      selectObject,
      removeObject,
      selectedRadiusM,
      onRunDetection,
    }
  },
}
</script>

<style scoped>
.detection-list-panel {
  margin-top: 10px;
  padding: 10px;
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 10px;
  background: rgba(69, 40, 8, 0.22);
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.kicker {
  display: block;
  color: #fbbf24;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.panel-head strong {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
}

.panel-head em {
  display: grid;
  place-items: center;
  min-width: 26px;
  height: 26px;
  padding: 0 7px;
  border-radius: 999px;
  background: rgba(251, 191, 36, 0.16);
  color: #fcd34d;
  font-style: normal;
  font-size: 0.7rem;
  font-weight: 800;
}

.object-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
  max-height: 220px;
  overflow: auto;
}

.object-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 8px;
  border: 1px solid #3a4f63;
  border-radius: 8px;
  background: rgba(15, 34, 54, 0.72);
  cursor: pointer;
}

.object-row.active,
.object-row:hover {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.12);
}

.risk-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 8px;
  border-radius: 50%;
  background: #22c55e;
}

.risk-dot.medium {
  background: #f59e0b;
}

.risk-dot.high {
  background: #ef4444;
}

.object-copy {
  min-width: 0;
  flex: 1 1 auto;
}

.object-copy strong {
  display: block;
  overflow: hidden;
  font-size: 0.74rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.object-copy small,
.empty,
.hint {
  color: #b7c7d6;
  font-size: 0.66rem;
}

.empty,
.hint {
  margin: 4px 0 0;
}

.delete-btn {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  border: 1px solid #5b3b3b;
  border-radius: 7px;
  background: rgba(220, 53, 69, 0.14);
  color: #fca5a5;
}

.delete-btn:disabled {
  opacity: 0.55;
}

.detect-action-wrap {
  margin-bottom: 8px;
}

.detect-controls-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.radius-select-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #fbbf24;
  font-size: 0.72rem;
}

.radius-select {
  padding: 4px 6px;
  border: 1px solid rgba(245, 158, 11, 0.4);
  border-radius: 6px;
  background: #0f172a;
  color: #f1f5f9;
  font-size: 0.72rem;
  outline: none;
}

.run-detect-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  flex: 1 1 auto;
  padding: 6px 10px;
  border: 1px solid #d97706;
  border-radius: 6px;
  background: linear-gradient(135deg, #b45309, #d97706);
  color: #fff;
  font-size: 0.74rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.run-detect-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #d97706, #f59e0b);
  border-color: #f59e0b;
}

.run-detect-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spin {
  display: inline-block;
  animation: spin-kf 1s linear infinite;
}

@keyframes spin-kf {
  100% {
    transform: rotate(360deg);
  }
}
</style>
