/**
 * Centralized Real-time Data Synchronization Service
 * Keeps data in sync across Analysis, Database, and Reports views.
 */
import { ref } from 'vue'

export const SCENARIO_STORAGE_KEY = 'weaponeering.activeScenarioId'

export const dataVersion = ref(1)

const listeners = new Set()

/**
 * Notify all subscribed views and windows that data has been modified.
 * @param {string} resource - Identifier of the changed resource (e.g. '/targets', '/scenarios', 'all')
 */
export function notifyDataChanged(resource = 'all') {
  dataVersion.value++
  listeners.forEach((callback) => {
    try {
      callback(resource)
    } catch (err) {
      console.warn('[dataSync] Callback error:', err)
    }
  })

  if (typeof window !== 'undefined') {
    window.dispatchEvent(
      new CustomEvent('weaponeering-data-changed', {
        detail: { resource, timestamp: Date.now() },
      })
    )
  }
}

/**
 * Subscribe to data change events.
 * Returns an unsubscribe cleanup function.
 * @param {Function} callback - Function called with (resource)
 * @returns {Function} cleanup
 */
export function onDataChanged(callback) {
  listeners.add(callback)

  let customListener = null
  if (typeof window !== 'undefined') {
    customListener = (event) => {
      try {
        callback(event.detail?.resource || 'all')
      } catch (err) {
        console.warn('[dataSync] Window event listener error:', err)
      }
    }
    window.addEventListener('weaponeering-data-changed', customListener)
  }

  return () => {
    listeners.delete(callback)
    if (customListener && typeof window !== 'undefined') {
      window.removeEventListener('weaponeering-data-changed', customListener)
    }
  }
}

// Listen to storage events across tabs/windows
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key === SCENARIO_STORAGE_KEY) {
      notifyDataChanged('scenario_storage')
    }
  })
}
