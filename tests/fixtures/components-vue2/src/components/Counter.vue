<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{ start: number }>();
const n = ref<number>(props.start);
</script>

<template>
  <button @click="n++">{{ n }}</button>
</template>
