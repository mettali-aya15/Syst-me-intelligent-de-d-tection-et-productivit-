<template>
  <div class="page">
    <h2>Machines</h2>

    <table class="machines-table">
      <thead>
        <tr>
          <th>Machine</th>
          <th>Type</th>
          <th>Production</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="m in machines" :key="m.id">
          <td>{{ m.name }}</td>
          <td>{{ m.type }}</td>
          <td>{{ m.count }}</td>
          <td>
            <span :class="['status', m.status]">
              {{ m.status }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { getMachines } from "../services/api"

const machines = ref(0)

onMounted(async () => {
  const res = await getMachines()
  machines.value = res.data.length
})
</script>

<style scoped>
.page {
  padding: 20px;
}
.machines-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}
th, td {
  padding: 12px;
  border-bottom: 1px solid #eee;
}
.status {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  color: white;
}
.running {
  background: #2ecc71;
}
.stopped {
  background: #e74c3c;
}
</style>
