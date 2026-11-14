<script setup lang="ts">
import Counter from "@/components/Counter.vue";
import Legacy from "@/components/Legacy.vue";
</script>

<template>
  <Counter :start="1" />
  <Legacy />
</template>

<style scoped>
div {
  margin: 0;
}
</style>
