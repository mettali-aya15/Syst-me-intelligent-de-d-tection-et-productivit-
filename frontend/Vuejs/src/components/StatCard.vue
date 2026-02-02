<template>
  <div class="card">
    <h4 class="title">{{ title }}</h4>
    <p class="value">{{ value }}</p>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: String,
    required: true
  }
})
</script>

<style scoped>
.card {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
  text-align: center;
}

.title {
  font-size: 14px;
  color: #7f8c8d;
  margin-bottom: 8px;
}

.value {
  font-size: 26px;
  font-weight: bold;
  color: #2c3e50;
}
</style>
