/** Parse / format target coordinates: WGS84 decimal, DMS, UTM and MGRS (all on the WGS84 datum). */

import { forward as mgrsForward, getLetterDesignator, toPoint as mgrsToPoint } from 'mgrs'

const WGS84_A = 6378137
const WGS84_F = 1 / 298.257223563
const UTM_K0 = 0.9996
const E2 = WGS84_F * (2 - WGS84_F)
const EP2 = E2 / (1 - E2)

const DEG = Math.PI / 180

function isValidLatLng(lat, lng) {
  return Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180
}

function utmCentralMeridian(zone) {
  return (zone - 1) * 6 - 180 + 3
}

export function latLngToUtm(lat, lng) {
  const zone = Math.min(60, Math.floor((lng + 180) / 6) + 1)
  const phi = lat * DEG
  const lambda = (lng - utmCentralMeridian(zone)) * DEG
  const sin = Math.sin(phi)
  const cos = Math.cos(phi)
  const tan = Math.tan(phi)
  const n = WGS84_A / Math.sqrt(1 - E2 * sin * sin)
  const t = tan * tan
  const c = EP2 * cos * cos
  const a = cos * lambda
  const m =
    WGS84_A *
    ((1 - E2 / 4 - (3 * E2 ** 2) / 64 - (5 * E2 ** 3) / 256) * phi -
      ((3 * E2) / 8 + (3 * E2 ** 2) / 32 + (45 * E2 ** 3) / 1024) * Math.sin(2 * phi) +
      ((15 * E2 ** 2) / 256 + (45 * E2 ** 3) / 1024) * Math.sin(4 * phi) -
      ((35 * E2 ** 3) / 3072) * Math.sin(6 * phi))
  const easting =
    UTM_K0 *
      n *
      (a + ((1 - t + c) * a ** 3) / 6 + ((5 - 18 * t + t * t + 72 * c - 58 * EP2) * a ** 5) / 120) +
    500000
  let northing =
    UTM_K0 *
    (m +
      n *
        tan *
        ((a * a) / 2 +
          ((5 - t + 9 * c + 4 * c * c) * a ** 4) / 24 +
          ((61 - 58 * t + t * t + 600 * c - 330 * EP2) * a ** 6) / 720))
  if (lat < 0) northing += 10000000
  return {
    zone,
    band: getLetterDesignator(lat),
    hemisphere: lat < 0 ? 'S' : 'N',
    easting,
    northing,
  }
}

export function utmToLatLng(zone, hemisphere, easting, northing) {
  const x = easting - 500000
  const y = hemisphere === 'S' ? northing - 10000000 : northing
  const m = y / UTM_K0
  const mu = m / (WGS84_A * (1 - E2 / 4 - (3 * E2 ** 2) / 64 - (5 * E2 ** 3) / 256))
  const e1 = (1 - Math.sqrt(1 - E2)) / (1 + Math.sqrt(1 - E2))
  const phi1 =
    mu +
    ((3 * e1) / 2 - (27 * e1 ** 3) / 32) * Math.sin(2 * mu) +
    ((21 * e1 ** 2) / 16 - (55 * e1 ** 4) / 32) * Math.sin(4 * mu) +
    ((151 * e1 ** 3) / 96) * Math.sin(6 * mu) +
    ((1097 * e1 ** 4) / 512) * Math.sin(8 * mu)
  const sin = Math.sin(phi1)
  const cos = Math.cos(phi1)
  const tan = Math.tan(phi1)
  const n1 = WGS84_A / Math.sqrt(1 - E2 * sin * sin)
  const t1 = tan * tan
  const c1 = EP2 * cos * cos
  const r1 = (WGS84_A * (1 - E2)) / (1 - E2 * sin * sin) ** 1.5
  const d = x / (n1 * UTM_K0)
  const lat =
    phi1 -
    ((n1 * tan) / r1) *
      ((d * d) / 2 -
        ((5 + 3 * t1 + 10 * c1 - 4 * c1 * c1 - 9 * EP2) * d ** 4) / 24 +
        ((61 + 90 * t1 + 298 * c1 + 45 * t1 * t1 - 252 * EP2 - 3 * c1 * c1) * d ** 6) / 720)
  const lng =
    (d -
      ((1 + 2 * t1 + c1) * d ** 3) / 6 +
      ((5 - 2 * c1 + 28 * t1 - 3 * c1 * c1 + 8 * EP2 + 24 * t1 * t1) * d ** 5) / 120) /
    cos
  return { lat: lat / DEG, lng: utmCentralMeridian(zone) + lng / DEG }
}

function parseMgrs(raw) {
  const compact = raw.replace(/\s+/g, '').toUpperCase()
  const match = compact.match(/^(\d{1,2})([C-HJ-NP-X])([A-HJ-NP-Z]{2})(\d*)$/)
  if (!match || match[4].length % 2 !== 0 || match[4].length > 10) return null
  try {
    const [lng, lat] = mgrsToPoint(compact)
    return isValidLatLng(lat, lng) ? { lat, lng, format: 'MGRS' } : null
  } catch {
    return null
  }
}

// "48P 519095 1582834", "48N 519095E 1582834N", "48 519095 1582834".
// N / S after the zone mean hemisphere; any other letter is the latitude band.
function parseUtm(raw) {
  const match = raw
    .trim()
    .toUpperCase()
    .match(/^(\d{1,2})\s*([C-HJ-NP-X])?[\s,]+(\d{5,7}(?:\.\d+)?)\s*M?E?[\s,]+(\d{1,8}(?:\.\d+)?)\s*M?N?$/)
  if (!match) return null
  const zone = Number(match[1])
  if (zone < 1 || zone > 60) return null
  const letter = match[2] || 'N'
  const hemisphere = letter === 'S' || (letter !== 'N' && letter < 'N') ? 'S' : 'N'
  const easting = Number(match[3])
  const northing = Number(match[4])
  if (easting < 100000 || easting > 900000 || northing > 10000000) return null
  const { lat, lng } = utmToLatLng(zone, hemisphere, easting, northing)
  return isValidLatLng(lat, lng) ? { lat, lng, format: 'UTM' } : null
}

function dmsComponent(text, hemispheres) {
  const re = new RegExp(
    `(\\d{1,3}(?:\\.\\d+)?)\\s*[°º:\\s]\\s*(?:(\\d{1,2}(?:\\.\\d+)?)\\s*['′:\\s]\\s*)?(?:(\\d{1,2}(?:\\.\\d+)?)\\s*(?:["″]|'')?\\s*)?([${hemispheres}])`,
    'i',
  )
  const altRe = new RegExp(`(\\d{1,3}(?:\\.\\d+)?)\\s*°?\\s*([${hemispheres}])`, 'i')
  const m = text.match(re) || text.match(altRe)
  if (!m) return null
  const hemi = (m.length === 5 ? m[4] : m[2]).toUpperCase()
  const deg = Number(m[1])
  const min = m.length === 5 ? Number(m[2] || 0) : 0
  const sec = m.length === 5 ? Number(m[3] || 0) : 0
  if (min >= 60 || sec >= 60) return null
  const value = deg + min / 60 + sec / 3600
  return /[SW]/.test(hemi) ? -value : value
}

function parseDms(raw) {
  if (!/[NS]/i.test(raw) || !/[EW]/i.test(raw)) return null
  const lat = dmsComponent(raw, 'NS')
  const lng = dmsComponent(raw, 'EW')
  if (lat == null || lng == null) return null
  return isValidLatLng(lat, lng) ? { lat, lng, format: 'DMS' } : null
}

function parseDecimal(raw) {
  const match = raw.trim().match(/^(-?\d{1,3}(?:\.\d+)?)\s*[,;\s]\s*(-?\d{1,3}(?:\.\d+)?)$/)
  if (!match) return null
  const lat = Number(match[1])
  const lng = Number(match[2])
  return isValidLatLng(lat, lng) ? { lat, lng, format: 'DD' } : null
}

/** Detect the coordinate format and return `{ lat, lng, format }` or null. */
export function parseCoordinateText(text) {
  const raw = String(text || '').trim()
  if (!raw) return null
  return parseMgrs(raw) || parseUtm(raw) || parseDms(raw) || parseDecimal(raw)
}

export const COORDINATE_FORMAT_LABELS = {
  DD: 'WGS84 (องศาทศนิยม)',
  DMS: 'WGS84 (องศา ลิปดา ฟิลิปดา)',
  UTM: 'UTM',
  MGRS: 'MGRS',
}

export function formatDecimal(lat, lng) {
  return `${lat.toFixed(6)}, ${lng.toFixed(6)}`
}

function dmsPart(value, pos, neg) {
  const hemi = value < 0 ? neg : pos
  const abs = Math.abs(value)
  let deg = Math.floor(abs)
  let min = Math.floor((abs - deg) * 60)
  let sec = (abs - deg - min / 60) * 3600
  if (sec >= 59.995) {
    sec = 0
    min += 1
  }
  if (min >= 60) {
    min = 0
    deg += 1
  }
  return `${deg}°${String(min).padStart(2, '0')}'${sec.toFixed(2).padStart(5, '0')}"${hemi}`
}

export function formatDms(lat, lng) {
  return `${dmsPart(lat, 'N', 'S')} ${dmsPart(lng, 'E', 'W')}`
}

export function formatUtm(lat, lng) {
  const utm = latLngToUtm(lat, lng)
  return `${utm.zone}${utm.band} ${Math.round(utm.easting)} ${Math.round(utm.northing)}`
}

export function formatMgrs(lat, lng) {
  const value = mgrsForward([lng, lat], 5)
  return value.replace(/^(\d{1,2}[A-Z])([A-Z]{2})(\d{5})(\d{5})$/, '$1 $2 $3 $4')
}

export function formatAllCoordinates(lat, lng) {
  if (!isValidLatLng(Number(lat), Number(lng))) return null
  const la = Number(lat)
  const lo = Number(lng)
  let mgrs = '—'
  try {
    mgrs = formatMgrs(la, lo)
  } catch {
    /* MGRS is undefined in the polar regions */
  }
  return { DD: formatDecimal(la, lo), DMS: formatDms(la, lo), UTM: formatUtm(la, lo), MGRS: mgrs }
}
