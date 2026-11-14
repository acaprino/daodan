<template>
  <div id="app" class="card" :class="{ active: on, 'is-wide': wide }">
    <p :class="[$style.title, on ? 'on' : 'off']" class="text">x</p>
    <span v-bind:class="color"></span>
    <Child />
  </div>
</template>

<script setup lang="ts">
import { Child } from './components'
const on = true
const wide = false
const color = 'red'
</script>

<style scoped>
.card { color: v-bind(color); }
.card :deep(.inner) { padding: 0; }
.on { font-weight: bold; }
</style>

<style module>
.title { font-size: 2em; }
</style>

<style lang="scss">
$pad: 4px;
.text { padding: $pad; }
</style>
