<template>
  <div>
    <h1>📊 Dashboard Global</h1>

    <div class="grid">
      <StatCard title="Productivité globale" value="82%" />
      <StatCard title="Machines actives" value="8 / 10" />
      <StatCard title="Alertes aujourd’hui" value="3" />
      <StatCard title="Temps idle total" value="1h 25m" />
    </div>

    <ProductivityChart />
  </div>
</template>

<script setup>
import StatCard from "../components/StatCard.vue"
import ProductivityChart from "../components/ProductivityChart.vue"
</script>

<style>
.grid {
  display:grid;
  grid-template-columns: repeat(4,1fr);
  gap:15px;
}
</style>
