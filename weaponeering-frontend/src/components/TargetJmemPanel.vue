<template>
  <section class="jmem-panel">
    <header class="jmem-head">
      <div>
        <span class="kicker">JMEM / สินค้า</span>
        <strong>{{ payload?.label || 'เป้าหมาย' }}</strong>
      </div>
      <button type="button" class="reload-btn" :disabled="loading" @click="load" title="รีเฟรช">
        <i class="bi" :class="loading ? 'bi-hourglass-split' : 'bi-arrow-clockwise'"></i>
      </button>
    </header>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="loading && !payload" class="muted">กำลังคำนวณ JMEM…</p>

    <template v-else-if="payload">
      <p class="hint">{{ payload.product_hint }}</p>

      <label class="selector">
        <span>เลือกสินค้า</span>
        <select :value="selectedId" :disabled="saving" @change="onSelectProduct">
          <option value="">— อัตโนมัติ (อันดับ JMEM) —</option>
          <option v-for="p in payload.product_catalog" :key="p.id" :value="p.id">
            {{ p.name }} ({{ formatWeight(p.weight_pounds) }})
          </option>
        </select>
      </label>

      <div v-if="topProduct" class="hero">
        <strong>{{ topProduct.product_name }}</strong>
        <small v-if="topProduct.description" class="product-desc">{{ topProduct.description }}</small>
        <small>
          Pd {{ formatPct(topProduct.pd_base) }} · Pk₁ {{ formatPct(topProduct.pk_single) }} ·
          Pk(N) {{ formatPct(previewPk) }}
          <template v-if="topProduct.impact_angle_deg">
            · มุมตก {{ Math.round(topProduct.impact_angle_deg) }}°
          </template>
        </small>
      </div>

      <div v-if="topProduct" class="quantity-row">
        <label class="quantity-field">
          <span>จำนวนลูก (N)</span>
          <input
            type="number"
            min="1"
            max="999"
            step="1"
            :value="quantityDraft"
            :disabled="saving"
            @input="onQuantityInput"
          />
        </label>
        <div class="quantity-meta">
          <small v-if="topProduct.n_jmem != null">
            JMEM แนะนำ N={{ topProduct.n_jmem }}
            <template v-if="quantityOverridden"> · ปรับแล้ว</template>
          </small>
          <small>Pk(N) {{ formatPct(previewPk) }}</small>
        </div>
        <div class="quantity-actions">
          <button
            type="button"
            class="qty-btn secondary"
            :disabled="saving || !quantityDirty"
            @click="resetQuantity"
          >
            ค่า JMEM
          </button>
          <button
            type="button"
            class="qty-btn primary"
            :disabled="saving || !quantityDirty"
            @click="saveQuantity"
          >
            บันทึก
          </button>
        </div>
      </div>

      <div class="product-list">
        <button
          v-for="item in displayProducts"
          :key="item.product_id"
          type="button"
          class="product-row"
          :class="{ selected: item.selected || item.product_id === selectedId }"
          @click="selectProduct(item.product_id)"
        >
          <span class="rank">#{{ item.rank }}</span>
          <span class="meta">
            <strong>{{ item.product_name }}</strong>
            <small>
              Pd {{ formatPct(item.pd_base) }} · N={{ item.n_required }} ·
              Pk {{ formatPct(item.pk_n) }} · {{ formatWeight(item.weight_pounds) }}
            </small>
          </span>
        </button>
        <p v-if="!displayProducts.length" class="muted">
          ยังไม่มีสินค้าใน Database (Wing Products) ของ scenario นี้
        </p>
      </div>

      <div v-if="payload.laser_designation" class="designation" :class="{ required: payload.laser_designation.required }">
        <span class="kicker">{{ payload.laser_designation.title }}</span>
        <p>{{ payload.laser_designation.intro }}</p>
        <ol v-if="payload.laser_designation.workflows?.length">
          <li v-for="flow in payload.laser_designation.workflows" :key="flow.key">
            <strong>{{ flow.label_th }} ({{ flow.label_en }})</strong>
            <span>{{ flow.summary }}</span>
          </li>
        </ol>
        <small v-if="payload.laser_designation.weather_limitation" class="weather">
          {{ payload.laser_designation.weather_limitation }}
        </small>
      </div>

      <div v-if="payload.weapon_effects" class="weapon-effects">
        <span class="kicker">{{ payload.weapon_effects.title }}</span>
        <p>{{ payload.weapon_effects.intro }}</p>
        <ol v-if="payload.weapon_effects.effects?.length">
          <li v-for="effect in payload.weapon_effects.effects" :key="effect.key">
            <strong>{{ effect.label_th }} ({{ effect.label_en }})</strong>
            <span>{{ effect.summary }}</span>
          </li>
        </ol>
      </div>

      <div v-if="payload.circular_error" class="circular-error">
        <span class="kicker">{{ payload.circular_error.title }}</span>
        <p>{{ payload.circular_error.intro }}</p>
        <ol v-if="payload.circular_error.metrics?.length">
          <li v-for="metric in payload.circular_error.metrics" :key="metric.key">
            <strong>{{ metric.label_th }} ({{ metric.label_en }})</strong>
            <span>{{ metric.summary }}</span>
          </li>
        </ol>
        <small v-if="payload.circular_error.ce50_ft != null && payload.circular_error.ce90_ft != null" class="cep-values">
          CE50 {{ payload.circular_error.ce50_ft.toFixed(0) }} ft ·
          CE90 {{ payload.circular_error.ce90_ft.toFixed(0) }} ft
          <template v-if="payload.circular_error.cep_source === 'weapon'"> · จากความแม่นยำระบบอาวุธ</template>
          <template v-else-if="payload.circular_error.cep_source === 'pilot'"> · จาก Pilot CEP</template>
        </small>
        <small v-if="payload.circular_error.application" class="application">
          {{ payload.circular_error.application }}
        </small>
      </div>

      <div v-if="payload.effect_zones?.length" class="zones">
        <span class="kicker">รัศมีผลกระทบ</span>
        <div v-for="z in payload.effect_zones" :key="z.zone" class="zone-row">
          <i :style="{ background: z.color }"></i>
          <span>{{ z.label_th }}</span>
          <em>{{ formatRadius(z.radius_m, z.radius_ft) }}</em>
        </div>
      </div>

      <div v-if="payload.warnings?.length" class="warnings">
        <span class="kicker">หมายเหตุ</span>
        <small v-for="(w, i) in payload.warnings" :key="i">{{ w }}</small>
      </div>

      <div v-if="payload.mission" class="mission">
        <span class="kicker">Mission inputs</span>
        <small>
          CEP {{ payload.mission.cep_ft.toFixed(0) }} ft ·
          TLE {{ payload.mission.tle_ft.toFixed(0) }} ft ·
          Desired Pk {{ formatPct(payload.mission.pk_desired) }}
        </small>
      </div>
    </template>
  </section>
</template>

<script>
import { computed, ref, watch } from 'vue'
import { apiJson, putResource } from '../services/api'
import { pkForRounds } from '../utils/jmemMath'

export default {
  name: 'TargetJmemPanel',
  props: {
    targetId: { type: String, default: '' },
    coordinateId: { type: String, default: '' },
  },
  emits: ['updated', 'error'],
  setup(props, { emit }) {
    const payload = ref(null)
    const loading = ref(false)
    const saving = ref(false)
    const error = ref('')
    const quantityDraft = ref(1)

    const activeScope = computed(() => {
      if (!payload.value) return null
      if (props.coordinateId) {
        const row = payload.value.coordinate_products?.find(
          (c) => c.coordinate_id === props.coordinateId,
        )
        return {
          weapon_quantity: row?.weapon_quantity ?? null,
          products: row?.products?.length ? row.products : payload.value.products || [],
        }
      }
      return {
        weapon_quantity: payload.value.weapon_quantity ?? null,
        products: payload.value.products || [],
      }
    })

    const selectedId = computed(() => {
      if (!payload.value) return ''
      if (props.coordinateId) {
        const row = payload.value.coordinate_products?.find(
          (c) => c.coordinate_id === props.coordinateId,
        )
        return row?.selected_product_id || payload.value.selected_product_id || ''
      }
      return payload.value.selected_product_id || ''
    })

    const displayProducts = computed(() => (activeScope.value?.products || []).slice(0, 8))

    const topProduct = computed(() => displayProducts.value[0] || null)

    const savedQuantity = computed(() => {
      const saved = activeScope.value?.weapon_quantity
      if (saved != null && Number(saved) >= 1) return Number(saved)
      return topProduct.value?.n_jmem ?? topProduct.value?.n_required ?? 1
    })

    const quantityDirty = computed(() => {
      const draft = Math.max(1, Math.floor(Number(quantityDraft.value) || 1))
      const saved = activeScope.value?.weapon_quantity
      if (saved == null) {
        const jmemN = topProduct.value?.n_jmem ?? topProduct.value?.n_required ?? 1
        return draft !== jmemN
      }
      return draft !== saved
    })

    const quantityOverridden = computed(() => {
      if (quantityDirty.value) return true
      return Boolean(topProduct.value?.quantity_overridden)
    })

    const previewPk = computed(() => {
      const product = topProduct.value
      if (!product) return 0
      const n = Math.max(1, Math.floor(Number(quantityDraft.value) || 1))
      return pkForRounds(product.pk_single, n)
    })

    function syncQuantityDraft() {
      quantityDraft.value = savedQuantity.value
    }

    async function load() {
      if (!props.targetId) {
        payload.value = null
        return
      }
      loading.value = true
      error.value = ''
      try {
        payload.value = await apiJson(`/jmem/targets/${props.targetId}`)
        syncQuantityDraft()
      } catch (err) {
        error.value = err.message || 'โหลด JMEM ไม่สำเร็จ'
        payload.value = null
        emit('error', error.value)
      } finally {
        loading.value = false
      }
    }

    async function selectProduct(productId) {
      if (!props.targetId || saving.value) return
      saving.value = true
      error.value = ''
      try {
        const body = {
          product_id: productId || null,
          coordinate_id: props.coordinateId || null,
        }
        payload.value = await putResource(
          `/jmem/targets/${props.targetId}/selected-product`,
          body,
        )
        syncQuantityDraft()
        emit('updated', payload.value)
      } catch (err) {
        error.value = err.message || 'บันทึกสินค้าไม่สำเร็จ'
        emit('error', error.value)
      } finally {
        saving.value = false
      }
    }

    function onQuantityInput(event) {
      const value = Math.max(1, Math.floor(Number(event.target.value) || 1))
      quantityDraft.value = value
      event.target.value = String(value)
    }

    async function saveQuantity() {
      if (!props.targetId || saving.value || !topProduct.value) return
      saving.value = true
      error.value = ''
      try {
        const quantity = Math.max(1, Math.floor(Number(quantityDraft.value) || 1))
        const body = {
          quantity,
          coordinate_id: props.coordinateId || null,
        }
        payload.value = await putResource(
          `/jmem/targets/${props.targetId}/weapon-quantity`,
          body,
        )
        syncQuantityDraft()
        emit('updated', payload.value)
      } catch (err) {
        error.value = err.message || 'บันทึกจำนวนลูกไม่สำเร็จ'
        emit('error', error.value)
      } finally {
        saving.value = false
      }
    }

    async function resetQuantity() {
      if (!props.targetId || saving.value) return
      saving.value = true
      error.value = ''
      try {
        const body = {
          quantity: null,
          coordinate_id: props.coordinateId || null,
        }
        payload.value = await putResource(
          `/jmem/targets/${props.targetId}/weapon-quantity`,
          body,
        )
        syncQuantityDraft()
        emit('updated', payload.value)
      } catch (err) {
        error.value = err.message || 'รีเซ็ตจำนวนลูกไม่สำเร็จ'
        emit('error', error.value)
      } finally {
        saving.value = false
      }
    }

    function onSelectProduct(event) {
      selectProduct(event.target.value || null)
    }

    function formatPct(value) {
      const n = Number(value)
      if (!Number.isFinite(n)) return '—'
      return `${(n * 100).toFixed(1)}%`
    }

    function formatWeight(lb) {
      const n = Number(lb)
      if (!Number.isFinite(n)) return '—'
      return `${Math.round(n)} lb`
    }

    function formatRadius(m, ft) {
      const meters = Number(m)
      const feet = Number(ft)
      if (!Number.isFinite(meters)) return '—'
      return `${meters.toFixed(1)} m (${feet.toFixed(0)} ft)`
    }

    watch(
      () => [props.targetId, props.coordinateId],
      () => load(),
      { immediate: true },
    )

    return {
      payload,
      loading,
      saving,
      error,
      selectedId,
      displayProducts,
      topProduct,
      quantityDraft,
      quantityDirty,
      quantityOverridden,
      previewPk,
      load,
      selectProduct,
      onSelectProduct,
      onQuantityInput,
      saveQuantity,
      resetQuantity,
      formatPct,
      formatWeight,
      formatRadius,
    }
  },
}
</script>

<style scoped>
.jmem-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
  padding: 10px;
  border: 1px solid rgba(103, 232, 249, 0.28);
  border-radius: 10px;
  background: rgba(8, 24, 36, 0.72);
  min-width: 0;
  box-sizing: border-box;
}

.jmem-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
}

.jmem-head div {
  min-width: 0;
  flex: 1 1 auto;
  overflow: hidden;
}

.jmem-head strong {
  display: block;
  margin-top: 2px;
  font-size: 0.82rem;
  line-height: 1.35;
  word-break: break-word;
  overflow-wrap: break-word;
}

.kicker {
  display: block;
  color: #67e8f9;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.reload-btn {
  flex: 0 0 28px;
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--control-bg);
  color: var(--text);
  cursor: pointer;
}

.hint,
.muted,
.error {
  font-size: 0.68rem;
  line-height: 1.45;
  word-break: break-word;
  overflow-wrap: break-word;
}

.hint,
.muted {
  color: var(--muted);
}

.error {
  color: #fca5a5;
}

.selector {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.7rem;
  color: #cbd5e1;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.selector select {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  padding: 6px 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--control-bg);
  color: var(--text);
  font-size: 0.74rem;
  outline: none;
  box-sizing: border-box;
}

.hero {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 8px;
  border-radius: 8px;
  background: rgba(103, 232, 249, 0.08);
  border: 1px solid rgba(103, 232, 249, 0.15);
  min-width: 0;
  box-sizing: border-box;
}

.hero strong {
  color: #67e8f9;
  font-size: 0.8rem;
  line-height: 1.35;
  word-break: break-word;
  overflow-wrap: break-word;
}

.hero small {
  color: var(--muted);
  font-size: 0.68rem;
  line-height: 1.45;
  word-break: break-word;
  overflow-wrap: break-word;
}

.hero .product-desc {
  color: #c5d4e4;
  line-height: 1.4;
  word-break: break-word;
  overflow-wrap: break-word;
}

.quantity-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
  border: 1px solid rgba(103, 232, 249, 0.22);
  border-radius: 8px;
  background: rgba(8, 24, 36, 0.55);
  min-width: 0;
  box-sizing: border-box;
}

.quantity-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.7rem;
  color: #cbd5e1;
  width: 100%;
  box-sizing: border-box;
}

.quantity-field input {
  width: 100%;
  max-width: 100%;
  padding: 6px 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--control-bg);
  color: var(--text);
  font-size: 0.78rem;
  outline: none;
  box-sizing: border-box;
}

.quantity-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px 8px;
  font-size: 0.66rem;
  color: var(--muted);
  line-height: 1.35;
  word-break: break-word;
}

.quantity-actions {
  display: flex;
  gap: 6px;
  width: 100%;
  box-sizing: border-box;
}

.qty-btn {
  flex: 1 1 0;
  min-width: 0;
  padding: 6px 8px;
  border-radius: 8px;
  font-size: 0.68rem;
  font-weight: 600;
  border: 1px solid var(--border);
  cursor: pointer;
  box-sizing: border-box;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.qty-btn.primary {
  background: rgba(103, 232, 249, 0.18);
  color: #e0f2fe;
  border-color: rgba(103, 232, 249, 0.45);
}

.qty-btn.secondary {
  background: var(--control-bg);
  color: var(--text);
}

.qty-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.product-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
  max-height: 220px;
  overflow-y: auto;
  overflow-x: hidden;
  min-width: 0;
  box-sizing: border-box;
}

.product-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  padding: 7px 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: rgba(13, 110, 253, 0.05);
  color: var(--text);
  text-align: left;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  cursor: pointer;
}

.product-row.selected {
  border-color: #67e8f9;
  background: rgba(103, 232, 249, 0.12);
}

.rank {
  flex: 0 0 24px;
  min-width: 24px;
  color: #67e8f9;
  font-size: 0.72rem;
  font-weight: 700;
}

.meta {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}

.meta strong {
  font-size: 0.74rem;
  line-height: 1.35;
  word-break: break-word;
  overflow-wrap: break-word;
}

.meta small {
  color: var(--muted);
  font-size: 0.66rem;
  line-height: 1.35;
  word-break: break-word;
  overflow-wrap: break-word;
}

.designation {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
  border: 1px solid rgba(103, 232, 249, 0.2);
  border-radius: 8px;
  background: rgba(8, 24, 36, 0.45);
  min-width: 0;
  box-sizing: border-box;
}

.designation.required {
  border-color: rgba(250, 204, 21, 0.28);
}

.designation p,
.designation li span,
.designation .weather {
  margin: 0;
  color: var(--muted);
  font-size: 0.68rem;
  line-height: 1.45;
  word-break: break-word;
  overflow-wrap: break-word;
}

.designation ol {
  margin: 0;
  padding-left: 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.designation li {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.designation li strong {
  color: #e8f0f8;
  font-size: 0.7rem;
  line-height: 1.35;
  word-break: break-word;
  overflow-wrap: break-word;
}

.designation .weather {
  color: #fcd34d;
}

.weapon-effects {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
  border: 1px solid rgba(248, 113, 113, 0.28);
  border-radius: 8px;
  background: rgba(36, 12, 12, 0.45);
  min-width: 0;
  box-sizing: border-box;
}

.weapon-effects p,
.weapon-effects li span {
  margin: 0;
  color: var(--muted);
  font-size: 0.68rem;
  line-height: 1.45;
  word-break: break-word;
  overflow-wrap: break-word;
}

.weapon-effects ol {
  margin: 0;
  padding-left: 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.weapon-effects li {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.weapon-effects li strong {
  color: #fecaca;
  font-size: 0.7rem;
  line-height: 1.35;
  word-break: break-word;
  overflow-wrap: break-word;
}

.circular-error {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
  border: 1px solid rgba(165, 180, 252, 0.32);
  border-radius: 8px;
  background: rgba(15, 18, 40, 0.5);
  min-width: 0;
  box-sizing: border-box;
}

.circular-error p,
.circular-error li span,
.circular-error .application,
.circular-error .cep-values {
  margin: 0;
  color: var(--muted);
  font-size: 0.68rem;
  line-height: 1.45;
  word-break: break-word;
  overflow-wrap: break-word;
}

.circular-error ol {
  margin: 0;
  padding-left: 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.circular-error li {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.circular-error li strong {
  color: #c7d2fe;
  font-size: 0.7rem;
  line-height: 1.35;
  word-break: break-word;
  overflow-wrap: break-word;
}

.circular-error .cep-values {
  color: #a5b4fc;
}

.circular-error .application {
  color: #c7d2fe;
}

.zones,
.warnings,
.mission {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  box-sizing: border-box;
}

.zone-row {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 0.7rem;
  min-width: 0;
  box-sizing: border-box;
}

.zone-row i {
  flex: 0 0 10px;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  border: 1px solid rgba(255, 255, 255, 0.35);
}

.zone-row span {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.zone-row em {
  flex: 0 0 auto;
  margin-left: auto;
  color: var(--muted);
  font-style: normal;
  white-space: nowrap;
  font-size: 0.68rem;
}

.warnings small,
.mission small {
  color: var(--muted);
  font-size: 0.66rem;
  line-height: 1.45;
  word-break: break-word;
  overflow-wrap: break-word;
}
</style>