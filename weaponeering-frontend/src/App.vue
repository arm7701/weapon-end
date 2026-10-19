<script>
export default {
  name: 'App'
}
</script>

<template>
  <div id="app">
    <router-view v-slot="{ Component, route }">
      <keep-alive :max="3" :exclude="['Login']">
        <component :is="Component" :key="route.name" />
      </keep-alive>
    </router-view>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  font-family: var(--font-sans, 'IBM Plex Sans Thai', 'Inter', 'Noto Sans Thai', 'Sarabun', 'Leelawadee UI', Tahoma, sans-serif);
  line-height: 1.55;
  letter-spacing: 0.012em;
  width: 100%;
  height: 100%;
}

body {
  background: #f5f5f5;
}

button,
input,
select,
textarea,
table,
dialog {
  font-family: inherit;
}

#app {
  width: 100%;
  height: 100vh;
}
</style>
