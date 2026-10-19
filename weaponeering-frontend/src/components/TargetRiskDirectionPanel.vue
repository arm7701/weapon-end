<template>
  <section v-if="selectedTargetId" class="risk-panel">
    <header class="risk-head">
      <span class="kicker">มุมออก / เข้า</span>
      <strong><i class="bi bi-compass"></i> ทิศทางเสี่ยงต่ำ</strong>
    </header>

    <template v-if="risk?.available">
      <div
        v-for="opt in options"
        :key="`${opt.rank}-${opt.bearingDeg}`"
        class="risk-option"
        :class="{ active: activeRank === Number(opt.rank) }"
      >
        <div class="option-row">
          <div class="option-copy">
            <strong>
              #{{ opt.rank }}
              {{ formatDeg(opt.bearingDeg) }}{{ opt.compassLabel || '' }}
              <template v-if="opt.ingressBearingDeg != null">
                → ออก {{ formatDeg(opt.ingressBearingDeg) }}
              </template>
            </strong>
            <small v-if="opt.riskScore != null">คะแนน {{ Number(opt.riskScore).toFixed(1) }}</small>
          </div>
          <button type="button" class="view-btn" @click="viewOption(opt)">
            {{ activeRank === Number(opt.rank) ? 'กำลังดู' : 'ดู' }}
          </button>
        </div>
        <p v-if="borderSummary(opt)" class="border-line">{{ borderSummary(opt) }}</p>
      </div>

      <p v-if="avoidText" class="avoid">{{ avoidText }}</p>
      <p v-for="(line, idx) in noteLines" :key="`note-${idx}`" class="note">{{ line }}</p>
    </template>

    <p v-else class="empty">
      {{ emptyMessage }}
    </p>
  </section>
</template>

<script>
import { computed, ref, watch } from 'vue'

function crossingText(prefix, crossing) {
  if (!crossing || typeof crossing !== 'object') return ''
  const dist =
    crossing.distanceNm != null ? `${Number(crossing.distanceNm).toFixed(1)}NM` : '—'
  const bear = crossing.bearingDeg != null ? `${Number(crossing.bearingDeg).toFixed(0)}°` : ''
  return `${prefix} ${dist} ${bear}`.trim()
}

export default {
  name: 'TargetRiskDirectionPanel',
  props: {
    targets: { type: Array, default: () => [] },
    selectedTargetId: { type: String, default: '' },
    selectedCoordinateId: { type: String, default: '' },
  },
  emits: ['view-ingress'],
  setup(props, { emit }) {
    const activeRank = ref(null)

    const selectedMarker = computed(() => {
      const list = props.targets || []
      if (!props.selectedTargetId) return null
      if (props.selectedCoordinateId) {
        const byCoord = list.find(
          (t) =>
            t.targetCardId === props.selectedTargetId &&
            t.coordinateId === props.selectedCoordinateId,
        )
        if (byCoord) return byCoord
      }
      return (
        list.find((t) => t.targetCardId === props.selectedTargetId && t.isPrimary) ||
        list.find((t) => t.targetCardId === props.selectedTargetId) ||
        null
      )
    })

    const risk = computed(() => selectedMarker.value?.lowestRiskDirection || null)

    const options = computed(() => {
      const recommended = risk.value?.recommendedOptions || []
      if (recommended.length) return recommended.slice(0, 3)
      if (risk.value?.bearingDeg == null) return []
      return [
        {
          rank: 1,
          bearingDeg: risk.value.bearingDeg,
          compassLabel: risk.value.compassLabel,
          riskScore: risk.value.riskScore,
          ingressBearingDeg: risk.value.ingressBearingDeg,
          borderRoute: risk.value.borderRoute,
        },
      ]
    })

    const avoidText = computed(() => {
      if (risk.value?.avoidBearingDeg == null) return ''
      let text = `หลีกเลี่ยง ${Number(risk.value.avoidBearingDeg).toFixed(0)}°${
        risk.value.avoidCompassLabel || ''
      }`
      if (risk.value.avoidRiskScore != null) {
        text += ` · ${Number(risk.value.avoidRiskScore).toFixed(1)}`
      }
      return text
    })

    const noteLines = computed(() => {
      const lines = risk.value?.recommendations || []
      return lines.filter((line) => {
        const text = String(line || '')
        if (!text) return false
        if (text.startsWith('ตัวเลือกที่แนะนำ') || text.startsWith('#')) return false
        if (/(เข้า|ออก|ขอบ|NM|°)/.test(text) && /Ingress|ทิศทาง/.test(text) === false) {
          // Keep general notes; skip duplicate route lines that mirror options.
          if (/^เข้า |^ออก |ขอบ /.test(text)) return false
        }
        return true
      })
    })

    const emptyMessage = computed(() => {
      const lines = risk.value?.recommendations || []
      if (lines.length) return String(lines[0])
      return 'รัน Detection เพื่อประเมินทิศทางออก–เข้า'
    })

    function formatDeg(value) {
      if (value == null || Number.isNaN(Number(value))) return '—'
      return `${Number(value).toFixed(0)}°`
    }

    function borderSummary(opt) {
      const route = opt?.borderRoute || {}
      if (!route.available) return route.message ? String(route.message) : ''
      const parts = []
      const nearest = route.nearestBorder
      if (nearest && typeof nearest === 'object') {
        parts.push(
          `ขอบ ${Number(nearest.distanceNm || 0).toFixed(1)}NM ${Number(
            nearest.bearingDeg || 0,
          ).toFixed(0)}°`,
        )
      }
      const entry = crossingText('ออก', route.entry)
      const exit = crossingText('เข้า', route.exit)
      if (entry) parts.push(entry)
      if (exit) parts.push(exit)
      if (route.totalCorridorNm != null) {
        parts.push(`รวม ${Number(route.totalCorridorNm).toFixed(1)}NM`)
      }
      return parts.join(' · ')
    }

    function viewOption(opt) {
      const rank = Number(opt?.rank || 0)
      activeRank.value = activeRank.value === rank ? null : rank
      emit('view-ingress', {
        targetCardId: props.selectedTargetId,
        coordinateId: props.selectedCoordinateId || selectedMarker.value?.coordinateId || null,
        rank: activeRank.value,
      })
    }

    watch(
      () => [props.selectedTargetId, props.selectedCoordinateId],
      () => {
        activeRank.value = null
      },
    )

    return {
      risk,
      options,
      avoidText,
      noteLines,
      emptyMessage,
      activeRank,
      formatDeg,
      borderSummary,
      viewOption,
    }
  },
}
</script>

<style scoped>
.risk-panel {
  margin-top: 10px;
  padding: 10px;
  border: 1px solid rgba(56, 189, 248, 0.28);
  border-radius: 10px;
  background: rgba(8, 47, 73, 0.28);
}

.risk-head {
  margin-bottom: 8px;
}

.kicker {
  display: block;
  color: #67e8f9;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.risk-head strong {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
}

.risk-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 6px;
  padding: 8px;
  border: 1px solid #2c445d;
  border-radius: 8px;
  background: rgba(15, 34, 54, 0.7);
}

.risk-option.active {
  border-color: #22d3ee;
  background: rgba(34, 211, 238, 0.1);
}

.option-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.option-copy {
  min-width: 0;
  flex: 1 1 auto;
}

.option-copy strong {
  display: block;
  font-size: 0.74rem;
  line-height: 1.35;
}

.option-copy small,
.border-line,
.avoid,
.note,
.empty {
  color: #9ec5d8;
  font-size: 0.68rem;
}

.border-line {
  margin: 0;
  line-height: 1.35;
}

.view-btn {
  flex: 0 0 auto;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid #355574;
  border-radius: 7px;
  background: #102336;
  color: #c8ddf3;
  font-family: inherit;
  font-size: 0.68rem;
  font-weight: 700;
}

.risk-option.active .view-btn {
  border-color: #22d3ee;
  background: rgba(34, 211, 238, 0.18);
  color: #ecfeff;
}

.avoid {
  margin: 8px 0 0;
}

.note {
  margin: 4px 0 0;
}

.empty {
  margin: 4px 0 0;
}
</style>
