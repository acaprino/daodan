<script setup lang="ts">
const count = ref(0)
function increment() {
  count.value++
}
function sendOrder() {
  return $fetch("/api/users", { method: "POST", body: { name: "x" } })
}
</script>
<template>
  <div>
    <h1>Home</h1>
    <button @click="increment">Add</button>
    <button @click="sendOrder">Send</button>
    <NuxtLink to="/about">About</NuxtLink>
  </div>
</template>
