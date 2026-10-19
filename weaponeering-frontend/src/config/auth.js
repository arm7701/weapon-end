/**
 * การตั้งค่าบริการยืนยันตัวตน RTAF Super App
 */
const apiBase = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

export const authConfig = Object.freeze({
  // POST application/json: { user: "ไม่ใส่ @rtaf.mi.th", pass: "OTP" }
  otpEndpoint: `${apiBase}/mfa/login`,
  otpCredentials: 'same-origin',
})
