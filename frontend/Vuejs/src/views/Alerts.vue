<template>
  <div>
    <h1>⚠️ Alertes</h1>

    <div
      v-for="a in alerts"
      :key="a.id"
      class="alert"
    >
      {{ a.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { subscribe, unsubscribe } from "../services/websocket"

const alerts = ref([])

function onEvent(data) {
  if (data.alert) {
    alerts.value.unshift({
      id: Date.now(),
      message: data.alert
    })
  }
}

onMounted(() => {
  subscribe(onEvent)
})

onUnmounted(() => {
  unsubscribe(onEvent)
})
</script>

<style>
.alert {
  background:#e74c3c;
  color:white;
  padding:12px;
  margin-bottom:10px;
  border-radius:6px;
}
</style>
