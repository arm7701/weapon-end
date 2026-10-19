/** Client-side JMEM helpers (mirror backend pk_for_rounds). */

export function pkForRounds(pkSingle, nRounds) {
  const pk = Number(pkSingle)
  const n = Math.max(0, Math.floor(Number(nRounds) || 0))
  if (n <= 0 || !Number.isFinite(pk) || pk <= 0) return 0
  if (pk >= 1) return 1
  return 1 - (1 - pk) ** n
}
