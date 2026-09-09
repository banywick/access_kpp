<!-- frontend/src/App.vue -->
<template>
  <div id="app">
    <Header v-if="!isWelcomePage" />
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
/* Импортируем глобальные стили */
@import './assets/styles/main.css';

#app {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.main-content.no-header {
  max-width: 100%;
  padding: 0;
  margin: 0;
}

/* Адаптивные отступы для контента */
@media (max-width: 768px) {
  .main-content {
    padding: 15px;
  }
}

@media (max-width: 480px) {
  .main-content {
    padding: 10px;
  }
}
</style>