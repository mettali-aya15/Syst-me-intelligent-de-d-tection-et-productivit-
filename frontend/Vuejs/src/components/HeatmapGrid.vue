<template>
  <div class="grid">
    <div
      v-for="cell in cells"
      :key="cell.id"
      class="cell"
      :style="{ background: getColor(cell.value) }"
    >
      {{ cell.name }}<br>{{ cell.value }}%
    </div>
  </div>
</template>

<script setup>
const cells = [
  { id:1, name:"M1", value:85 },
  { id:2, name:"M2", value:60 },
  { id:3, name:"M3", value:92 },
  { id:4, name:"M4", value:45 }
]

function getColor(val) {
  if (val > 80) return "#2ecc71"
  if (val > 60) return "#f1c40f"
  return "#e74c3c"
}
</script>

<style>
.grid {
  display:grid;
  grid-template-columns: repeat(4,1fr);
  gap:10px;
}
.cell {
  padding:20px;
  color:white;
  font-weight:bold;
  border-radius:8px;
  text-align:center;
}
</style>
