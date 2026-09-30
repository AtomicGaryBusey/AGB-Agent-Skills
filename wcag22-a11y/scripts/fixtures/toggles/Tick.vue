<template>
  <div class="opts">
    <label class="tick">
      <input class="tick-native" type="checkbox" v-model="pickup">
      <span class="tick-box"></span>
      Collect from the depot
    </label>
  </div>
</template>

<script>
export default { data() { return { pickup: false }; } };
</script>

<style scoped>
.opts { background: #fafafa; }
.tick-native { clip: rect(0 0 0 0); clip-path: inset(50%); position: absolute; width: 1px; height: 1px; overflow: hidden; }
.tick-box { display: inline-block; width: 18px; height: 18px; border: 2px solid #cfcfcf; border-radius: 3px; }
.tick-native:checked ~ .tick-box { background: #3a3a3a; border-color: #3a3a3a; }
</style>
