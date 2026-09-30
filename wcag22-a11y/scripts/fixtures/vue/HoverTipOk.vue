<template>
  <div class="rate-row">
    <label for="rate">Hourly rate</label>
    <input id="rate" class="rate-field" type="number" aria-describedby="rate-hint">
    <span class="hint-wrap" @mouseenter="showHint = true" @mouseleave="showHint = false">
      <button type="button" class="hint-trigger" aria-label="About rates"
              @focus="showHint = true" @blur="showHint = false" @keydown.esc="showHint = false">i</button>
      <span v-show="showHint" id="rate-hint" role="tooltip" class="hint-bubble">Rates include VAT.</span>
    </span>
  </div>
</template>

<script>
export default {
  data() { return { showHint: false }; },
};
</script>

<style scoped>
.rate-field { border: 1px solid #767676; padding: 4px; }
</style>
