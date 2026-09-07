<!-- frontend/src/App.vue -->
<template>
  <div id="app">
    <Header />
    <main class="main-content" :class="{ 'no-header': isWelcomePage }">
      <router-view />
    </main>
    <Footer v-if="!isWelcomePage" />
  </div>
</template>

<script>
import Header from './components/common/Header.vue'
import Footer from './components/common/Footer.vue'

export default {
  name: 'App',
  components: {
    Header,
    Footer
  },
  computed: {
    isWelcomePage() {
      return this.$route.path === '/'
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  background: #f5f7fa;
  color: #2c3e50;
  -webkit-font-smoothing: antialiased;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.main-content.no-header {
  max-width: 100%;
  margin: 0;
}

@media (max-width: 768px) {
  .main-content {
    padding: 0 15px;
  }
}

@media (max-width: 480px) {
  .main-content {
    padding: 0 10px;
  }
}
</style>