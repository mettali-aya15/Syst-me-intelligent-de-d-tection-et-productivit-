<template>
  <div>
    <h1>📅 Rapport Journalier</h1>

    <table>
      <thead>
        <tr>
          <th>Machine</th>
          <th>Production</th>
          <th>Productivité</th>
          <th>Temps Idle</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="m in machines" :key="m.name">
          <td>{{ m.name }}</td>
          <td>{{ m.output }}</td>
          <td>{{ m.rate }}%</td>
          <td>{{ m.idle }} min</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
const machines = [
  { name:"Sewing 1", output:320, rate:85, idle:12 },
  { name:"Sewing 2", output:260, rate:70, idle:35 },
  { name:"Knitting 1", output:410, rate:92, idle:8 }
]
</script>

<style>
table {
  width:100%;
  background:white;
  border-collapse:collapse;
}
th, td {
  padding:10px;
  border-bottom:1px solid #eee;
}
</style>
