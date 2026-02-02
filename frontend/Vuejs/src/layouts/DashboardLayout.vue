<template>
  <div class="layout">
    <aside>
      <h2>🏭 Factory IA</h2>
      <button @click="page='overview'">Dashboard</button>
      <button @click="page='machines'">Machines</button>
      <button @click="page='heatmap'">Heatmap</button>
      <button @click="page='alerts'">Alertes</button>
    </aside>

    <main>
      <Overview v-if="page==='overview'" />
      <Machines v-if="page==='machines'" />
      <Heatmap v-if="page==='heatmap'" />
      <Alerts v-if="page==='alerts'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Overview from '../views/Overview.vue'
import Machines from '../views/Machines.vue'
import Heatmap from '../views/Heatmap.vue'
import Alerts from '../views/Alerts.vue'

const page = ref("overview")
</script>

<style>
.layout { display:flex; height:100vh }
aside {
  width:220px;
  background:#2c3e50;
  color:white;
  padding:15px;
}
aside button {
  width:100%;
  margin-bottom:10px;
}
main { flex:1; padding:20px; background:#f4f6f9 }
</style>
