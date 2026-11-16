<script setup lang="ts">
import { ref } from "vue";
const n = ref(0);
function inc(by: number) { n.value += by; }
function label(v: number) { return String(v); }
const items = [{ id: 1, name: "a" }];
</script>

<template>
  <button @click="inc(1)" :title="label(n)">{{ n }}</button>
  <li v-for="item in items" :key="item.id">{{ label(item.id) }} {{ item.name }}</li>
</template>
