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
      <div class="radius-control-row">
        <label class="radius-label" title="รัศมีการตรวจจับรอบเป้าหมาย (ม.)">
          <i class="bi bi-bullseye"></i>
          <span>รัศมีตรวจจับ:</span>
        </label>
        <select v-model.number="selectedRadiusM" :disabled="detecting" class="radius-select">
          <option :value="50">50 ม.</option>
          <option :value="100">100 ม.</option>
          <option :value="120">120 ม. (มาตรฐาน)</option>
          <option :value="200">200 ม.</option>
          <option :value="300">300 ม.</option>
        </select>
      </div>

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

    <p v-if="!filteredDetections.length" class="empty">
      ยังไม่มีอาคาร detection ของเป้าหมายนี้
    </p>

    <div v-else>
      <p v-if="hasNearbyCarryover" class="carryover-note">
        <i class="bi bi-info-circle"></i> ตรวจพบอาคารในรัศมี (คำนวณระดับความเสี่ยงตามระยะจุดนี้แล้ว)
      </p>
      <div class="object-list">
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
              <template v-if="item.distanceM != null">
                · {{ item.distanceM }} ม.
              </template>
              <template v-if="item.confidence != null">
                · {{ Math.round(Number(item.confidence) * 100) }}%
              </template>
              <template v-if="item.isNearbyCarryover">
                · <span class="nearby-tag">ในรัศมี</span>
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
    targetLat: { type: Number, default: null },
    targetLng: { type: Number, default: null },
    detecting: { type: Boolean, default: false },
  },
  emits: ['deleted', 'select-object', 'error', 'run-detection'],
  setup(props, { emit }) {
    const deletingId = ref('')
    const selectedObjectId = ref('')
    const message = ref('')
    const selectedRadiusM = ref(120)

    function distanceM(lat1, lng1, lat2, lng2) {
      const meanLat = ((lat1 + lat2) / 2) * (Math.PI / 180)
      const dLat = (lat2 - lat1) * 111320
      const dLng = (lng2 - lng1) * 111320 * Math.max(Math.cos(meanLat), 0.1)
      return Math.hypot(dLat, dLng)
    }

    function calculateRiskForDistance(dist, radiusM) {
      if (dist <= radiusM * 0.35) return 'high'
      if (dist <= radiusM * 0.70) return 'medium'
      return 'low'
    }

    function onRunDetection() {
      message.value = 'กำลังจัดมุมกล้องและส่งตรวจจับอาคารด้วย building-seg.pt…'
      emit('run-detection', {
        radiusM: selectedRadiusM.value,
        coordinateId: props.selectedCoordinateId,
        model: 'Building Detector',
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

      const targetDetections = list.filter(
        (x) => x.targetCardId === props.selectedTargetId,
      )

      if (
        props.targetLat == null ||
        props.targetLng == null ||
        targetDetections.length === 0
      ) {
        return targetDetections
      }

      const scanRadius = selectedRadiusM.value
      const items = []
      for (const d of targetDetections) {
        if (d.lat == null || d.lng == null) {
          items.push(d)
          continue
        }
        const dist = Math.round(
          distanceM(props.targetLat, props.targetLng, d.lat, d.lng),
        )
        if (dist <= scanRadius) {
          const isFromOtherCoord =
            props.selectedCoordinateId &&
            d.targetCoordinateId &&
            d.targetCoordinateId !== props.selectedCoordinateId
          items.push({
            ...d,
            distanceM: dist,
            risk: calculateRiskForDistance(dist, scanRadius),
            isNearbyCarryover: Boolean(isFromOtherCoord),
          })
        }
      }
      return items
    })

    const hasNearbyCarryover = computed(() =>
      filteredDetections.value.some((x) => x.isNearbyCarryover),
    )

    function riskLabel(risk) {
      return RISK_LABELS[risk] || RISK_LABELS.low
    }

    function selectObject(item) {
      selectedObjectId.value = item.id
      emit('select-object', item)
    }

    async function removeObject(item) {
      if (!item?.id) return
      deletingId.value = item.id
      try {
        await deleteResource('detection-objects', item.id)
        emit('deleted', item.id)
      } catch (err) {
        emit('error', err.message || 'ลบวัตถุไม่สำเร็จ')
      } finally {
        deletingId.value = ''
      }
    }

    return {
      deletingId,
      selectedObjectId,
      message,
      filteredDetections,
      hasNearbyCarryover,
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
  border: 1px solid rgba(245, 158, 11, 0.35);
  border-radius: 10px;
  background: rgba(245, 158, 11, 0.05);
  display: flex;
  flex-direction: column;
  min-width: 0;
  box-sizing: border-box;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  min-width: 0;
}

.panel-head div {
  min-width: 0;
  flex: 1 1 auto;
}

.kicker {
  display: block;
  color: #f59e0b;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.panel-head strong {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
  line-height: 1.35;
  word-break: break-word;
}

.panel-head em {
  display: grid;
  place-items: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
  font-style: normal;
  font-size: 0.72rem;
  font-weight: 700;
  flex: 0 0 auto;
}

.detect-action-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 10px;
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
}

.radius-control-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.radius-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #fbbf24;
  font-size: 0.74rem;
  font-weight: 500;
  flex: 0 0 auto;
  white-space: nowrap;
}

.radius-select {
  flex: 1 1 auto;
  min-width: 0;
  max-width: 100%;
  padding: 6px 8px;
  border: 1px solid rgba(245, 158, 11, 0.4);
  border-radius: 6px;
  background: #0f172a;
  color: #f1f5f9;
  font-size: 0.72rem;
  outline: none;
  box-sizing: border-box;
}

.run-detect-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d97706;
  border-radius: 6px;
  background: linear-gradient(135deg, #b45309, #d97706);
  color: #fff;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  box-sizing: border-box;
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

.object-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
  max-height: 220px;
  overflow-y: auto;
  overflow-x: hidden;
  min-width: 0;
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
  min-width: 0;
  box-sizing: border-box;
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
  flex: 1 1 0;
  min-width: 0;
  overflow: hidden;
}

.object-copy strong {
  display: block;
  overflow: hidden;
  font-size: 0.74rem;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.object-copy small {
  display: block;
  overflow: hidden;
  font-size: 0.66rem;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #b7c7d6;
}

.empty,
.hint {
  color: #b7c7d6;
  font-size: 0.66rem;
  line-height: 1.45;
  word-break: break-word;
  overflow-wrap: break-word;
  margin: 4px 0 0;
}

.delete-btn {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  flex: 0 0 26px;
  border: 1px solid #5b3b3b;
  border-radius: 7px;
  background: rgba(220, 53, 69, 0.14);
  color: #fca5a5;
  margin-left: auto;
}

.delete-btn:disabled {
  opacity: 0.55;
}

.carryover-note {
  margin: 0 0 8px;
  padding: 5px 8px;
  background: rgba(30, 58, 138, 0.35);
  border: 1px solid rgba(59, 130, 246, 0.4);
  border-radius: 6px;
  font-size: 0.69rem;
  line-height: 1.4;
  word-break: break-word;
  overflow-wrap: break-word;
  color: #93c5fd;
  display: flex;
  align-items: center;
  gap: 6px;
}

.nearby-tag {
  display: inline-block;
  padding: 1px 4px;
  background: rgba(59, 130, 246, 0.25);
  border: 1px solid rgba(59, 130, 246, 0.5);
  border-radius: 3px;
  color: #bfdbfe;
  font-size: 0.62rem;
  font-weight: 600;
}

@keyframes spin-kf {
  100% {
    transform: rotate(360deg);
  }
}
</style>
