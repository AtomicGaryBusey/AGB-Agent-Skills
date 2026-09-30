<template>
  <div class="rate-row">
    <label for="rate">Hourly rate</label>
    <input id="rate" class="rate-field" type="number">
    <span class="hint-trigger" tabindex="0" role="button" aria-label="About rates"
          @mouseenter="showHint = true" @mouseleave="showHint = false"
          @focus="showHint = true" @blur="showHint = false">i</span>
    <p v-show="showHint" class="hint-bubble">Rates include VAT.</p>
  </div>
</template>

<script>
export default {
  data() { return { showHint: false }; },
};
</script>

<style scoped>
.rate-field { border: 1px solid #dddddd; padding: 4px; }
</style>
