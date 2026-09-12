<template>
  <IndexLight v-if="currentView === 'home'" @go-workbench="goWorkbench" />
  <Workbench v-else @go-home="goHome" />
</template>

<script>
import IndexLight from './components/IndexLight.vue'
import Workbench from './components/Workbench.vue'

export default {
  name: 'App',
  components: { IndexLight, Workbench },
  data() {
    return {
      currentView: 'home'
    }
  },
  methods: {
    goWorkbench() {
      this.currentView = 'workbench'
    },
    goHome() {
      this.currentView = 'home'
    }
  }
}
</script>

<style>
*, *::before, *::after { box-sizing: border-box; }
html, body { margin: 0; padding: 0; overflow-x: hidden; }
#app {
  font-family: "DIN Alternate", "Bahnschrift", "Segoe UI", "Microsoft YaHei", sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  width: 100vw;
}
</style>
