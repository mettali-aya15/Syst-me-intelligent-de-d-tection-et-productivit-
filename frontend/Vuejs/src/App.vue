<template>
  <Login v-if="!isAuthenticated" />
  <DashboardLayout v-else />
</template>


<script setup>
import DashboardLayout from "./layouts/DashboardLayout.vue"
</script>

<style>
/* Reset simple + style global */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: "Segoe UI", Arial, sans-serif;
  background-color: #f4f6f9;
}
</style>
