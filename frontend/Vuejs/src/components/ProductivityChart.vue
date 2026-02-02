<template>
  <canvas ref="chart"></canvas>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import Chart from 'chart.js/auto'

const chart = ref(null)

onMounted(() => {
  new Chart(chart.value, {
    type: 'bar',
    data: {
      labels: ['Machine 1', 'Machine 2', 'Machine 3'],
      datasets: [{
        label: 'Productivité %',
        data: [82, 65, 90]
      }]
    }
  })
})
</script>
