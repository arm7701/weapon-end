<template>
  <nav class="navbar navbar-expand-xl top-header" :class="isDarkMode ? 'navbar-dark' : 'navbar-light'">
    <div class="container-fluid header-container">
      <router-link to="/analysis" class="system-brand">
        <span class="logo-frame">
          <img :src="logoUrl" alt="กองบัญชาการควบคุมการปฏิบัติทางอากาศ" class="system-logo" />
        </span>
        <span class="brand-copy">
          <strong>WEAPONEERING SYSTEM</strong>
          <small>ระบบสนับสนุนการวิเคราะห์เป้าหมาย</small>
        </span>
      </router-link>

      <button class="navbar-toggler header-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-label="เปิดเมนู">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarNav">
        <div class="navbar-nav main-navigation ms-xl-4">
          <router-link to="/analysis" class="nav-link system-nav-link">
            <i class="bi bi-graph-up-arrow"></i><span>วิเคราะห์</span>
          </router-link>
          <router-link to="/database" class="nav-link system-nav-link">
            <i class="bi bi-database-gear"></i><span>ฐานข้อมูล</span>
          </router-link>
          <router-link to="/reports" class="nav-link system-nav-link">
            <i class="bi bi-file-earmark-text"></i><span>รายงาน บันทึกข้อมูล</span>
          </router-link>
        </div>

        <div class="header-tools ms-auto">
          <button class="header-icon-button" @click="toggleTheme" :title="isDarkMode ? 'สลับเป็นโหมดสว่าง' : 'สลับเป็นโหมดดำ'">
            <i :class="isDarkMode ? 'bi bi-moon-stars' : 'bi bi-sun'" aria-hidden="true"></i>
          </button>

          <div class="date-time-chip">
            <i class="bi bi-clock"></i><span>{{ currentDateTime }}</span>
          </div>

          <div class="user-menu">
            <span class="user-avatar"><i class="bi bi-person"></i></span>
            <span class="user-copy"><small>ผู้ใช้งาน</small><strong>{{ userName }}</strong></span>
          </div>
          <button type="button" class="logout-button" title="ออกจากระบบ" aria-label="ออกจากระบบ" @click="logout">
            <i class="bi bi-box-arrow-right"></i>
            <span>Logout</span>
          </button>

        </div>
      </div>
    </div>
  </nav>
</template>

<script>
import { ref, onMounted, onUnmounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { getAuthUser, clearAuth } from '../services/auth'

export default {
  name: 'Header',
  setup() {
    const router = useRouter()
    const currentDateTime = ref('')
    const userName = ref(getAuthUser() || 'ผู้ใช้งาน')
    const isDarkMode = ref(true)
    const logoUrl = `${import.meta.env.BASE_URL}images/command-logo.png`
    let intervalId = null

    const applyTheme = (theme) => {
      const isDark = theme === 'dark'
      isDarkMode.value = isDark
      document.body.classList.toggle('dark-theme', isDark)
      document.body.classList.toggle('light-theme', !isDark)
      window.localStorage.setItem('app-theme', theme)
    }

    const updateDateTime = () => {
      const now = new Date()
      const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }
      currentDateTime.value = now.toLocaleString('th-TH', options)
    }

    const toggleTheme = () => {
      const nextTheme = isDarkMode.value ? 'light' : 'dark'
      applyTheme(nextTheme)
    }

    const logout = (e) => {
      e.preventDefault()
      if (confirm('คุณแน่ใจว่าต้องการออกจากระบบ?')) {
        clearAuth()
        router.replace('/login')
      }
    }

    onMounted(() => {
      userName.value = getAuthUser() || 'ผู้ใช้งาน'
      updateDateTime()
      intervalId = setInterval(updateDateTime, 1000)
      const storedTheme = window.localStorage.getItem('app-theme')
      applyTheme(storedTheme === 'light' ? 'light' : 'dark')
    })

    onActivated(() => {
      const storedTheme = window.localStorage.getItem('app-theme')
      applyTheme(storedTheme === 'light' ? 'light' : 'dark')
    })

    onUnmounted(() => {
      if (intervalId) clearInterval(intervalId)
    })

    return {
      currentDateTime,
      userName,
      isDarkMode,
      logoUrl,
      toggleTheme,
      logout
    }
  }
}
</script>

<style scoped>
.top-header {
  position: relative;
  z-index: 100;
  min-height: 74px;
  padding: 7px 0;
  border-bottom: 1px solid rgba(80, 133, 207, 0.38);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.22);
}

:global(body.dark-theme .top-header) {
  background: linear-gradient(90deg, #050d19, #081a31 55%, #071425) !important;
}

:global(body.light-theme .top-header) {
  background: linear-gradient(90deg, #ffffff, #f2f6fc) !important;
}

.header-container {
  gap: 16px;
  padding-right: 18px;
  padding-left: 18px;
}

.system-brand {
  display: inline-flex;
  align-items: center;
  min-width: 265px;
  gap: 11px;
  color: var(--text);
  text-decoration: none;
}

.logo-frame {
  display: inline-flex;
  flex: 0 0 54px;
  align-items: center;
  justify-content: center;
  width: 54px;
  height: 54px;
  padding: 2px;
  border: 1px solid rgba(238, 193, 64, 0.65);
  border-radius: 50%;
  background: #081a3a;
  box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.12), 0 5px 14px rgba(0, 0, 0, 0.3);
}

.system-logo {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: contain;
}

.brand-copy {
  display: flex;
  flex-direction: column;
}

.brand-copy strong {
  color: #ffd84d;
  font-size: 1.15rem;
  line-height: 1.3;
  letter-spacing: 0.065em;
  text-shadow: 0 1px 0 #7a4c00, 0 2px 7px rgba(255, 193, 7, 0.48);
}

.brand-copy small {
  color: #ffe78a;
  font-size: 0.76rem;
  font-weight: 600;
  line-height: 1.35;
  letter-spacing: 0.015em;
  text-shadow: 0 1px 0 #614000, 0 2px 6px rgba(255, 193, 7, 0.36);
}

:global(body.light-theme .brand-copy strong) {
  color: #9a6200;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.9), 0 2px 5px rgba(154, 98, 0, 0.2);
}

:global(body.light-theme .brand-copy small) {
  color: #6f5200;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.85);
}

.main-navigation {
  display: flex;
  flex-direction: row;
  gap: 6px;
  padding: 4px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: rgba(13, 110, 253, 0.045);
}

.system-nav-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 38px;
  padding: 7px 13px !important;
  border: 0 !important;
  border-radius: 7px;
  font-size: 0.8rem;
  font-weight: 500;
  white-space: nowrap;
  transition: background-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
}

.system-nav-link:hover {
  background: rgba(13, 110, 253, 0.12);
  color: #6ea8fe !important;
}

.system-nav-link.router-link-exact-active {
  background: #0d6efd !important;
  box-shadow: 0 4px 12px rgba(13, 110, 253, 0.32);
  color: #ffffff !important;
  transform: translateY(-1px);
}

.header-tools {
  display: flex;
  align-items: center;
  gap: 9px;
}

.header-icon-button,
.user-menu,
.logout-button {
  border: 1px solid var(--border);
  background: var(--control-bg);
  color: var(--text);
  font-family: inherit;
}

.header-icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 9px;
}

.header-icon-button:hover {
  border-color: #0d6efd;
  color: #6ea8fe;
}

.date-time-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 38px;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: 9px;
  background: var(--control-bg);
  color: var(--muted);
  font-size: 0.7rem;
  white-space: nowrap;
}

.date-time-chip i {
  color: #6ea8fe;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 7px;
  min-height: 40px;
  padding: 4px 10px 4px 5px;
  border-radius: 9px;
}

.logout-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 40px;
  padding: 6px 10px;
  border-color: rgba(220, 53, 69, 0.54);
  border-radius: 9px;
  color: #ef6b78;
  font-size: 0.7rem;
  font-weight: 600;
}

.logout-button:hover {
  border-color: #dc3545;
  background: #dc3545;
  color: #ffffff;
}

.user-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 7px;
  background: rgba(13, 110, 253, 0.16);
  color: #6ea8fe;
}

.user-copy {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.1;
}

.user-copy small {
  color: var(--muted);
  font-size: 0.58rem;
}

.user-copy strong {
  font-size: 0.72rem;
}

.header-toggler {
  border-color: var(--border);
}

@media (max-width: 1199.98px) {
  .navbar-collapse {
    padding: 12px 0 5px;
  }

  .main-navigation {
    margin-bottom: 10px;
  }

  .header-tools {
    flex-wrap: wrap;
    justify-content: flex-end;
  }
}

@media (max-width: 620px) {
  .top-header {
    min-height: 58px;
    padding: 5px 0;
  }

  .header-container {
    gap: 8px;
    padding-right: 10px;
    padding-left: 10px;
  }

  .system-brand {
    min-width: 0;
    max-width: calc(100% - 54px);
    gap: 8px;
  }

  .logo-frame {
    flex-basis: 44px;
    width: 44px;
    height: 44px;
  }

  .brand-copy small,
  .date-time-chip {
    display: none;
  }

  .logout-button span {
    display: none;
  }

  .brand-copy strong {
    overflow: hidden;
    max-width: 205px;
    font-size: 0.82rem;
    letter-spacing: 0.035em;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .header-toggler {
    width: 40px;
    height: 40px;
    padding: 5px 7px;
  }

  .navbar-collapse {
    padding-top: 9px;
  }

  .main-navigation {
    width: 100%;
  }

  .system-nav-link {
    flex: 1 1 0;
    min-height: 44px;
    padding: 8px 7px;
  }

  .header-tools {
    width: 100%;
    justify-content: space-between;
    gap: 7px;
  }

  .header-icon-button,
  .logout-button {
    min-width: 42px;
    min-height: 42px;
  }

  .user-menu {
    flex: 1 1 auto;
    min-width: 0;
  }

  .user-copy {
    min-width: 0;
  }

  .user-copy strong {
    overflow: hidden;
    display: block;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
