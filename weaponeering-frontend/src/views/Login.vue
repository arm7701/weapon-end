<template>
  <div class="login-view" :style="pageStyle">
    <div class="page">
      <main class="page-content container-fluid p-0 row g-0 m-0">
        <section
          class="visual-side col-lg-6 d-none d-lg-block"
          aria-label="Weaponeering System Secure Decision Support Platform"
        >
          <div class="visual-brand">
            <img :src="logoUrl" alt="ตราสัญลักษณ์ Weaponeering System">
            <h2>WEAPONEERING SYSTEM</h2>
            <p>Secure Decision Support Platform</p>
          </div>
        </section>

        <section class="login-side col-12 col-lg-6">
          <div class="login-card">
            <header class="card-header login-header">
              <img class="mobile-login-logo" :src="logoUrl" alt="ตราสัญลักษณ์ Weaponeering System">
              <h2>เข้าสู่ระบบ</h2>
            </header>
            <div class="header-rule"></div>

            <form class="login-form" novalidate @submit.prevent="submitOtpLogin">
              <div class="field-group">
                <label class="field-label" for="email">
                  <svg class="field-title-icon" viewBox="0 0 24 24" aria-hidden="true">
                    <rect x="3" y="5" width="18" height="14" rx="2"></rect>
                    <path d="m4 7 8 6 8-6"></path>
                  </svg>
                  Email
                </label>
                <span class="input-wrap">
                  <input
                    id="email"
                    v-model="email"
                    type="text"
                    inputmode="email"
                    autocomplete="username"
                    autocapitalize="none"
                    spellcheck="false"
                    placeholder="ไม่ต้องกรอก @rtaf.mi.th"
                    maxlength="80"
                    required
                    @blur="email = normalizeUser(email)"
                  >
                </span>
              </div>

              <div class="field-group">
                <label class="field-label section-title" id="otp-label">OTP จาก Super App</label>
                <div
                  class="otp-boxes"
                  role="group"
                  aria-labelledby="otp-label"
                >
                  <input
                    v-for="(_, index) in otpDigits"
                    :key="index"
                    :ref="(el) => setOtpRef(el, index)"
                    :id="index === 0 ? 'otp-0' : undefined"
                    class="otp-digit"
                    type="text"
                    inputmode="numeric"
                    autocomplete="one-time-code"
                    maxlength="1"
                    pattern="[0-9]"
                    :aria-label="`รหัส OTP หลักที่ ${index + 1}`"
                    :value="otpDigits[index]"
                    @input="onOtpInput(index, $event)"
                    @keydown="onOtpKeydown(index, $event)"
                    @paste="onOtpPaste($event)"
                    @focus="onOtpFocus(index, $event)"
                  >
                </div>
              </div>

              <button class="login-button" type="submit" :disabled="loginPending">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M10 17l5-5-5-5M15 12H3M14 3h4a3 3 0 0 1 3 3v12a3 3 0 0 1-3 3h-4"></path>
                </svg>
                <span>เข้าสู่ระบบ</span>
              </button>
              <p class="message" :class="{ error: messageIsError }" aria-live="polite">{{ message }}</p>
            </form>
          </div>
        </section>
      </main>

      <footer class="page-footer">
        <span class="developer-credit d-none d-sm-inline-flex">
          <img class="developer-credit-logo" :src="creditLogoUrl" alt="โลโก้ศูนย์ซอฟต์แวร์กองทัพอากาศ">
          <span>พัฒนาโดยศูนย์ซอฟต์แวร์กองทัพอากาศ</span>
        </span>
        <span>Version 1.0.0</span>
      </footer>
    </div>
  </div>
</template>

<script>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authConfig } from '../config/auth'
import { setAuth } from '../services/auth'
import './login/LoginPage.css'

const OTP_LENGTH = 6

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const base = import.meta.env.BASE_URL || '/'
    const logoUrl = `${base}images/weaponeering-logo.png`
    const creditLogoUrl = `${base}images/software-center-logo.png`
    const pageStyle = computed(() => ({
      '--login-bg-image': `url(${base}images/background.png)`,
    }))

    const email = ref('')
    const otpDigits = ref(Array.from({ length: OTP_LENGTH }, () => ''))
    const otpInputs = ref([])
    const message = ref('')
    const messageIsError = ref(false)
    const loginPending = ref(false)

    const otp = computed(() => otpDigits.value.join(''))

    const setOtpRef = (el, index) => {
      if (el) otpInputs.value[index] = el
    }

    const focusOtp = (index) => {
      const input = otpInputs.value[Math.max(0, Math.min(OTP_LENGTH - 1, index))]
      input?.focus()
      input?.select?.()
    }

    const clearOtp = () => {
      otpDigits.value = Array.from({ length: OTP_LENGTH }, () => '')
    }

    const applyOtpValue = (value, startIndex = 0) => {
      const digits = String(value || '').replace(/\D/g, '').slice(0, OTP_LENGTH - startIndex).split('')
      if (!digits.length) return startIndex

      const next = [...otpDigits.value]
      digits.forEach((digit, offset) => {
        next[startIndex + offset] = digit
      })
      otpDigits.value = next

      const filledUntil = startIndex + digits.length
      return filledUntil >= OTP_LENGTH ? OTP_LENGTH - 1 : filledUntil
    }

    const onOtpInput = (index, event) => {
      const raw = event.target.value.replace(/\D/g, '')
      if (!raw) {
        otpDigits.value[index] = ''
        return
      }

      const focusIndex = applyOtpValue(raw, index)
      event.target.value = otpDigits.value[index]
      nextTick(() => focusOtp(focusIndex))
    }

    const onOtpKeydown = (index, event) => {
      if (event.key === 'Backspace') {
        if (otpDigits.value[index]) {
          otpDigits.value[index] = ''
          return
        }
        if (index > 0) {
          event.preventDefault()
          otpDigits.value[index - 1] = ''
          focusOtp(index - 1)
        }
        return
      }

      if (event.key === 'ArrowLeft' && index > 0) {
        event.preventDefault()
        focusOtp(index - 1)
        return
      }

      if (event.key === 'ArrowRight' && index < OTP_LENGTH - 1) {
        event.preventDefault()
        focusOtp(index + 1)
      }
    }

    const onOtpPaste = (event) => {
      event.preventDefault()
      const pasted = event.clipboardData?.getData('text') || ''
      const focusIndex = applyOtpValue(pasted, 0)
      nextTick(() => focusOtp(focusIndex))
    }

    const onOtpFocus = (index, event) => {
      event.target.select()
      // ถ้าช่องก่อนหน้าว่าง ให้โฟกัสช่องว่างแรกแทน
      const firstEmpty = otpDigits.value.findIndex((digit) => !digit)
      if (firstEmpty !== -1 && firstEmpty < index) {
        focusOtp(firstEmpty)
      }
    }

    const showMessage = (text, isError = false) => {
      message.value = text
      messageIsError.value = isError
    }

    const normalizeUser = (value) =>
      String(value || '').trim().toLowerCase().replace(/@rtaf\.mi\.th$/i, '')

    const responseMessage = (data, fallback) => {
      if (!data) return fallback
      if (typeof data === 'string') return data.slice(0, 240) || fallback
      if (Array.isArray(data.detail)) {
        return data.detail.map((item) => item.msg || JSON.stringify(item)).join(', ') || fallback
      }
      if (typeof data.detail === 'string') return data.detail
      return data.message || data.error || fallback
    }

    const readResponse = async (response) => {
      if (response.status === 204) return null
      const text = await response.text()
      if (!text) return null
      try {
        return JSON.parse(text)
      } catch {
        return text
      }
    }

    const completeLogin = async (profile) => {
      const displayName = profile?.user_name || profile?.user || 'ผู้ใช้งาน'
      setAuth(displayName, profile)
      await router.replace('/analysis')
    }

    const submitOtpLogin = async () => {
      const user = normalizeUser(email.value)
      const pass = otp.value

      if (!/^[a-z0-9._-]+$/i.test(user)) {
        showMessage('กรุณากรอกชื่ออีเมล ทอ. โดยไม่ต้องใส่ @rtaf.mi.th', true)
        return
      }

      if (!/^\d{6}$/.test(pass)) {
        showMessage('กรุณากรอก OTP จาก RTAF Super App ให้ครบ 6 หลัก', true)
        const firstEmpty = otpDigits.value.findIndex((digit) => !digit)
        focusOtp(firstEmpty === -1 ? 0 : firstEmpty)
        return
      }

      if (!authConfig.otpEndpoint || String(authConfig.otpEndpoint).includes('REPLACE_')) {
        showMessage('ยังไม่ได้กำหนด OTP endpoint ในไฟล์ config', true)
        return
      }

      loginPending.value = true
      showMessage('กำลังตรวจสอบ OTP กับ RTAF Super App...')

      try {
        const response = await fetch(authConfig.otpEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: authConfig.otpCredentials || 'omit',
          cache: 'no-store',
          body: JSON.stringify({ user, pass }),
        })
        const data = await readResponse(response)

        if (!response.ok) {
          throw new Error(responseMessage(data, 'อีเมลหรือ OTP ไม่ถูกต้อง'))
        }

        const explicitlyRejected = data && typeof data === 'object' && (
          data.success === false || data.ok === false || data.status === 'error'
        )
        if (explicitlyRejected) {
          throw new Error(responseMessage(data, 'อีเมลหรือ OTP ไม่ถูกต้อง'))
        }

        clearOtp()
        showMessage('ยืนยันตัวตนสำเร็จ กำลังเปิดระบบ...')
        await completeLogin(data && typeof data === 'object' ? data : { user })
      } catch (error) {
        const networkError = error instanceof TypeError
        showMessage(
          networkError
            ? 'เชื่อมต่อเซิร์ฟเวอร์ Login ไม่ได้ กรุณาตรวจสอบว่า npm run dev ยังทำงานอยู่'
            : error.message,
          true,
        )
        clearOtp()
        nextTick(() => focusOtp(0))
        loginPending.value = false
      }
    }

    onMounted(() => {
      document.documentElement.classList.add('login-active')
      document.body.classList.add('login-active')
    })

    onUnmounted(() => {
      document.documentElement.classList.remove('login-active')
      document.body.classList.remove('login-active')
    })

    return {
      pageStyle,
      logoUrl,
      creditLogoUrl,
      email,
      otpDigits,
      message,
      messageIsError,
      loginPending,
      setOtpRef,
      onOtpInput,
      onOtpKeydown,
      onOtpPaste,
      onOtpFocus,
      normalizeUser,
      submitOtpLogin,
    }
  },
}
</script>
